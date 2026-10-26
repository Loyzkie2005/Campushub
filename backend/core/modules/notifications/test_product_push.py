"""No real Firebase sends: verify actual owners, sessions and committed approvals."""
import hashlib
import json
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import jwt
from django.conf import settings
from django.core.management import call_command
from django.db import connection, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department, User
from api.models import CampusHubUser, Product, ProductApprovalPush, PushDeviceRegistration, SellerRequest
from modules.messages.auth import mobile_chat_token, admin_chat_token
from modules.notifications.services.push_service import dispatch_delivery, send_to_installation


@override_settings(CAMPUSHUB_FCM_ENABLED=True)
class ProductApprovalPushTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        self.admin = User.objects.create_superuser(username="push-admin", role="Super Admin")
        self.owner = CampusHubUser.objects.create(username="push-owner", email="owner@example.test",
            first_name="Owner", last_name="Test", password_hash="unused", role="User", user_type="student")
        self.other = CampusHubUser.objects.create(username="push-other", email="other@example.test",
            first_name="Other", last_name="Test", password_hash="unused", role="User", user_type="student")
        SellerRequest.objects.create(mobile_user=self.owner, status="approved")
        self.product = Product.objects.create(mobile_seller=self.owner, name="Isolated pending listing",
            department=Department.objects.get(code="BSIT"), price=25, stock=5)
        self.url = reverse("mobile_push_device")
        self.token = mobile_chat_token(self.owner)
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + self.token}
        self.fid = "isolated_installation_12345"

    def register(self, **extra):
        return self.client.post(self.url, json.dumps({"installation_id": self.fid, **extra}),
                                content_type="application/json", **self.auth)

    def approve(self):
        self.register()
        self.product.approve(self.admin)
        return ProductApprovalPush.objects.get(product=self.product)

    def test_registration_requires_mobile_bearer_and_active_account(self):
        self.assertEqual(self.client.post(self.url).status_code, 401)
        self.assertEqual(self.client.post(self.url, HTTP_AUTHORIZATION="Bearer invalid").status_code, 401)
        self.assertEqual(self.client.post(self.url, HTTP_AUTHORIZATION="Bearer " + admin_chat_token(self.admin)).status_code, 401)
        self.owner.is_suspended = True
        self.owner.save(update_fields=["is_suspended"])
        self.assertEqual(self.register().status_code, 403)

    def test_registration_ignores_claimed_user_and_uses_verified_expiry(self):
        self.assertEqual(self.register(user_id=self.other.pk).status_code, 200)
        device = PushDeviceRegistration.objects.get()
        self.assertEqual(device.user, self.owner)
        self.assertEqual(device.session_digest, hashlib.sha256(self.token.encode()).hexdigest())
        self.assertGreater(device.valid_until, timezone.now())
        self.assertNotEqual(device.session_digest, self.token)
        self.register()
        self.assertEqual(PushDeviceRegistration.objects.count(), 1)

    def test_bad_json_fid_and_expired_sessions_are_rejected(self):
        for body in ("[1]", "invalid", '{"installation_id":"bad"}'):
            self.assertEqual(self.client.post(self.url, body, content_type="application/json", **self.auth).status_code, 400)
        claims = jwt.decode(self.token, settings.CHAT_JWT_SECRET, algorithms=["HS256"], audience="campushub-chat")
        claims["exp"] = int((timezone.now() - timedelta(seconds=1)).timestamp())
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + jwt.encode(claims, settings.CHAT_JWT_SECRET, algorithm="HS256")}
        self.assertEqual(self.register().status_code, 401)
        self.assertFalse(PushDeviceRegistration.objects.exists())

    def test_account_reassignment_and_old_logout_cannot_disable_new_owner(self):
        self.register()
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + mobile_chat_token(self.other)}
        self.register()
        self.client.delete(self.url, json.dumps({"installation_id": self.fid}),
                           content_type="application/json", HTTP_AUTHORIZATION="Bearer " + self.token)
        device = PushDeviceRegistration.objects.get()
        self.assertEqual(device.user, self.other)
        self.assertTrue(device.is_active)
        self.client.delete(self.url, json.dumps({"installation_id": self.fid}),
                           content_type="application/json", **self.auth)
        device.refresh_from_db()
        self.assertFalse(device.is_active)

    def test_old_session_logout_cannot_disable_same_users_new_session(self):
        self.register()
        claims = jwt.decode(self.token, settings.CHAT_JWT_SECRET, algorithms=["HS256"], audience="campushub-chat")
        claims["jti"] = "isolated-new-login"
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + jwt.encode(claims, settings.CHAT_JWT_SECRET, algorithm="HS256")}
        self.register()
        self.client.delete(self.url, json.dumps({"installation_id": self.fid}), content_type="application/json",
                           HTTP_AUTHORIZATION="Bearer " + self.token)
        self.assertTrue(PushDeviceRegistration.objects.get().is_active)

    def test_approval_queues_exact_owner_once_without_network_and_rolls_back(self):
        with patch("modules.notifications.services.push_service.send_to_installation") as send:
            delivery = self.approve()
            self.assertEqual(delivery.recipient, self.owner)
            self.product.approve(self.admin)
            self.assertEqual(ProductApprovalPush.objects.count(), 1)
            send.assert_not_called()
        self.product.refresh_from_db()
        self.assertEqual(delivery.approved_at, self.product.approved_at)

    def test_rolled_back_approval_has_no_delivery_or_status_change(self):
        self.register()
        try:
            with transaction.atomic():
                self.product.approve(self.admin)
                raise ValueError("Isolated rollback")
        except ValueError:
            pass
        self.product.refresh_from_db()
        self.assertEqual(self.product.approval_status, "pending")
        self.assertFalse(ProductApprovalPush.objects.exists())

    def test_no_device_or_web_seller_never_maps_by_email(self):
        self.product.approve(self.admin)
        web = Product.objects.create(seller=self.admin, name="Web listing", price=10)
        web.approve(self.admin)
        self.assertFalse(ProductApprovalPush.objects.exists())

    def test_worker_sends_only_once_and_keeps_product_state(self):
        delivery = self.approve()
        with patch("modules.notifications.services.push_service.send_to_installation", return_value="test-message") as send, \
             patch("modules.notifications.management.commands.send_product_approval_pushes.close_old_connections"):
            # Preserve TestCase's outer transaction; real workers run separately.
            call_command("send_product_approval_pushes", stdout=StringIO())
            self.assertEqual(dispatch_delivery(delivery.pk), "ignored")
            send.assert_called_once_with(self.fid, product_id=self.product.pk,
                recipient_id=self.owner.pk, delivery_id=delivery.pk,
                decision="approved", product_name=self.product.name)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "sent")
        self.assertIsNotNone(delivery.sent_at)
        self.product.refresh_from_db()
        self.assertEqual(self.product.approval_status, "approved")

    def test_failure_retries_without_failing_the_approved_product(self):
        delivery = self.approve()
        with patch("modules.notifications.services.push_service.send_to_installation", side_effect=RuntimeError("test-only")):
            self.assertEqual(dispatch_delivery(delivery.pk), "failed")
        delivery.refresh_from_db()
        self.assertEqual(delivery.attempts, 1)
        self.assertEqual(delivery.error_code, "send_failed")
        self.assertGreater(delivery.retry_at, timezone.now())
        self.product.refresh_from_db()
        self.assertEqual(self.product.approval_status, "approved")

    def test_device_or_session_changes_skip_queued_deliveries(self):
        for change in ({"is_active": False}, {"user_id": self.other.pk},
                       {"session_digest": "new-session"}, {"valid_until": timezone.now() - timedelta(seconds=1)}):
            with self.subTest(change=change):
                ProductApprovalPush.objects.all().delete()
                self.product.approval_status = "pending"
                self.product.save(update_fields=["approval_status"])
                delivery = self.approve()
                PushDeviceRegistration.objects.filter(pk=delivery.device_id).update(**change)
                with patch("modules.notifications.services.push_service.send_to_installation") as send:
                    self.assertEqual(dispatch_delivery(delivery.pk), "skipped")
                    send.assert_not_called()

    def test_revoked_seller_is_skipped(self):
        delivery = self.approve()
        SellerRequest.objects.filter(mobile_user=self.owner).update(is_suspended=True)
        with patch("modules.notifications.services.push_service.send_to_installation") as send:
            self.assertEqual(dispatch_delivery(delivery.pk), "skipped")
            send.assert_not_called()

    def test_archived_product_is_skipped(self):
        delivery = self.approve()
        self.product.archive()
        with patch("modules.notifications.services.push_service.send_to_installation") as send:
            self.assertEqual(dispatch_delivery(delivery.pk), "skipped")
            send.assert_not_called()

    def test_unregistered_firebase_device_is_deactivated(self):
        from firebase_admin import messaging
        delivery = self.approve()
        with patch("modules.notifications.services.push_service.send_to_installation",
                   side_effect=messaging.UnregisteredError("Isolated unavailable device")):
            self.assertEqual(dispatch_delivery(delivery.pk), "skipped")
        delivery.device.refresh_from_db()
        self.assertFalse(delivery.device.is_active)

    @override_settings(CAMPUSHUB_FCM_ENABLED=False)
    def test_disabled_sending_does_not_contact_firebase(self):
        delivery = self.approve()
        with patch("modules.notifications.services.push_service.send_to_installation") as send:
            self.assertEqual(dispatch_delivery(delivery.pk), "disabled")
            send.assert_not_called()
        delivery.refresh_from_db()
        self.assertEqual(delivery.attempts, 0)

    def test_firebase_payload_uses_fid_high_channel_and_current_product(self):
        with patch("modules.notifications.services.push_service._firebase_app", return_value=object()), \
             patch("firebase_admin.messaging.send", return_value="isolated-message") as send:
            send_to_installation(self.fid, product_id=1, recipient_id=self.owner.pk,
                                delivery_id=2, product_name=self.product.name)
        message = send.call_args.args[0]
        self.assertEqual(message.fid, self.fid)
        self.assertIsNone(message.token)
        self.assertEqual(message.notification.title, "Product Approved!")
        self.assertEqual(message.data["recipient_id"], str(self.owner.pk))
        self.assertIn(self.product.name, message.notification.body)
        self.assertEqual(message.android.notification.channel_id, "campushub_approvals_v1")
        self.assertEqual(message.android.priority, "high")
        self.assertEqual(message.android.notification.priority, "high")
        self.assertTrue(message.android.notification.default_sound)
        self.assertEqual(message.android.notification.visibility, "private")
        self.assertEqual(message.android.notification.icon, "ic_stat_campushub")

    def test_rejection_queues_once_and_repeated_rejection_only_updates_reason(self):
        self.register()
        self.product.reject(self.admin, "Please update the photo.")
        delivery = ProductApprovalPush.objects.get()
        self.assertEqual(delivery.decision, "rejected")
        timestamp = delivery.approved_at
        self.product.reject(self.admin, "Updated reason")
        self.assertEqual(ProductApprovalPush.objects.count(), 1)
        self.assertEqual(self.product.approved_at, timestamp)
        with patch("modules.notifications.services.push_service.send_to_installation") as send:
            self.assertEqual(dispatch_delivery(delivery.pk), "sent")
            self.assertEqual(send.call_args.kwargs['decision'], "rejected")

    def test_ordinary_save_has_no_new_review_and_superseded_decision_is_skipped(self):
        delivery = self.approve()
        self.product.description = "Updated details"
        self.product.save(update_fields=["description"])
        self.assertEqual(ProductApprovalPush.objects.count(), 1)
        self.product.reject(self.admin, "Review changed")
        self.assertEqual(ProductApprovalPush.objects.count(), 2)
        with patch("modules.notifications.services.push_service.send_to_installation") as send:
            self.assertEqual(dispatch_delivery(delivery.pk), "skipped")
            send.assert_not_called()

    def test_rejection_rollback_does_not_queue_or_change_product(self):
        self.register()
        with self.assertRaises(ValueError):
            with transaction.atomic():
                self.product.reject(self.admin, "Isolated")
                raise ValueError("Rollback")
        self.product.refresh_from_db()
        self.assertEqual(self.product.approval_status, "pending")
        self.assertFalse(ProductApprovalPush.objects.exists())

    def test_rejection_payload_contains_target_and_no_private_rejection_notes(self):
        with patch("modules.notifications.services.push_service._firebase_app", return_value=object()), \
             patch("firebase_admin.messaging.send", return_value="isolated-message") as send:
            send_to_installation(self.fid, product_id=self.product.pk, recipient_id=self.owner.pk,
                                 delivery_id=2, decision="rejected", product_name=self.product.name)
        message = send.call_args.args[0]
        self.assertEqual(message.data['type'], "product_rejected")
        self.assertEqual(message.data['product_id'], str(self.product.pk))
        self.assertEqual(message.notification.title, "Product Rejected")
        self.assertIn("has been rejected", message.notification.body)

    def test_owned_product_api_includes_rejected_listing_but_not_another_sellers(self):
        self.product.reject(self.admin, "Please update the photo.")
        other = Product.objects.create(mobile_seller=self.other, name="Other private listing", price=10)
        response = self.client.get('/api/seller/products/submit/', **self.auth)
        self.assertEqual(response.status_code, 200)
        rows = response.json()['products']
        self.assertEqual([p['id'] for p in rows], [self.product.pk])
        self.assertEqual(rows[0]['rejection_reason'], "Please update the photo.")


class ApprovalCommitVisibilityTests(SimpleTestCase):
    # Explicitly clean only this probe's committed fixtures. A global flush of
    # this legacy database cannot truncate managed users with unmanaged FKs.
    databases = {"default"}

    def test_separate_worker_connection_cannot_see_uncommitted_approval(self):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        owner, _ = CampusHubUser.objects.get_or_create(username="commit-owner", defaults={
            "email": "commit@example.test", "first_name": "Commit", "last_name": "Test", "password_hash": "unused"})
        product = Product.objects.create(mobile_seller=owner, name="Commit fixture", price=10)
        PushDeviceRegistration.objects.create(user=owner, installation_id="commit_installation_12345",
            session_digest="fixture", valid_until=timezone.now() + timedelta(hours=1))
        probe = connection.copy(alias="push_commit_probe")
        try:
            with transaction.atomic():
                product.approve(None)
                with probe.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM campushub_product_approval_push WHERE product_id = %s", [product.pk])
                    self.assertEqual(cursor.fetchone()[0], 0)
            with probe.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM campushub_product_approval_push WHERE product_id = %s", [product.pk])
                self.assertEqual(cursor.fetchone()[0], 1)
        finally:
            probe.close()
            Product.objects.filter(pk=product.pk).delete()
            PushDeviceRegistration.objects.filter(user=owner).delete()
            # This probe created no bookings. Avoid ORM traversal into absent
            # unmanaged legacy tables while deleting this exact test-only row.
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM campushub_user WHERE id = %s", [owner.pk])
