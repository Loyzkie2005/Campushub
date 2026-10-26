"""Recovery and contextual actions tested on isolated DB records; SMTP is mocked."""
import json
import os
from pathlib import Path
from datetime import timedelta
from django.core import signing
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.test import TestCase, Client, override_settings
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from api.models import CampusHubUser, PasswordResetCode, SellerRequest
from .models import AccountActivity, User, AdminTabToken
from .test_marketplace_support import MarketplaceSupportTests


@override_settings(CAMPUSHUB_PUBLIC_BASE_URL="https://campushub.example")
class AccountRecoveryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()
    setUp = MarketplaceSupportTests.setUp

    def request_recovery(self, purpose="password", account=None, action="assist_recovery"):
        account = account or self.local
        source = "admin" if isinstance(account, User) else "mobile"
        return self.client.post(reverse("admin_users_action"), {"action": action,
            "confirm_reset": "1", "account_ref": f"{source}:{account.pk}", "recovery_purpose": purpose})

    def delivery(self, purpose="password", account=None):
        with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True) as sender:
            target = account or self.local
            headers = {}
            if purpose == "email_verification":
                from modules.messages.auth import mobile_chat_token
                headers["HTTP_AUTHORIZATION"] = "Bearer " + mobile_chat_token(target)
            response = self.client.post(reverse("mobile_password_reset"), json.dumps({"email": target.email, "purpose": purpose}),
                content_type="application/json", **headers)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(sender.called)
        # Legacy owner-page compatibility only: construct an old signed URL in the test.
        # New delivery must never generate or email a URL.
        self.assertNotIn("link", sender.call_args.kwargs)
        row = PasswordResetCode.objects.latest("pk")
        return reverse("account_recovery", kwargs={"token": signing.dumps(row.pk, salt="campushub-account-recovery")}), sender.call_args.kwargs["code"]

    def test_action_triggers_and_context_menu(self):
        response = self.client.get(reverse("admin_users_page"))
        html = response.content.decode()
        table = html[html.index('<tbody>'):html.index('</tbody>')]
        self.assertEqual(table.count('class="icon-action'), 2)
        self.assertIn('view-user-btn', table)
        self.assertIn('View User', table)
        self.assertIn('View Activity', table)
        self.assertIn('Assist Account Recovery', table)
        self.assertNotIn('Edit Account', table); self.assertNotIn('Change Admin Role', table)
        self.assertNotIn('Deactivate Account', table)
        self.assertNotIn('name="new_password"', html)

    def test_unverified_email_requires_owner_verification(self):
        self.local.email_verified = False; self.local.save()
        with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True) as sender:
            self.request_recovery(); self.assertFalse(sender.called)
        link, code = self.delivery("email_verification")
        self.assertNotContains(Client().get(link), self.local.username)
        response = Client().post(link, {"code": code})
        self.assertContains(response, "Email verified")
        self.local.refresh_from_db(); self.assertTrue(self.local.email_verified)
        self.assertTrue(PasswordResetCode.objects.get().used)
        self.assertContains(Client().post(link, {"code": code}), "already used")

    def test_username_requires_code_and_is_single_use(self):
        link, code = self.delivery("username")
        owner = Client()
        self.assertNotContains(owner.get(link), self.local.username)
        self.assertNotContains(owner.post(link, {"code": "bad"}), self.local.username)
        self.assertContains(owner.post(link, {"code": code}), self.local.username)
        self.assertNotContains(owner.get(link), self.local.username)
        self.assertTrue(AccountActivity.objects.filter(activity_type="USERNAME_RECOVERY_COMPLETED").exists())

    def test_password_proof_is_bound_to_owner_browser(self):
        previous = self.local.password_hash
        link, code = self.delivery()
        owner, stranger = Client(), Client()
        owner.post(link, {"code": code})
        self.assertContains(owner.get(link), "New Password")
        self.assertNotContains(stranger.get(link), 'name="new_password"')
        stranger.post(link, {"new_password": "IntruderSecret7!", "confirm_password": "IntruderSecret7!"})
        self.local.refresh_from_db(); self.assertEqual(self.local.password_hash, previous)
        self.assertContains(owner.post(link, {"new_password": "OwnerChooses7!", "confirm_password": "OtherPassword7!"}), "do not match")
        owner.post(link, {"new_password": "OwnerChooses7!", "confirm_password": "OwnerChooses7!"})
        self.local.refresh_from_db(); self.assertTrue(check_password("OwnerChooses7!", self.local.password_hash))
        self.assertContains(owner.get(link), "already used")
        self.assertNotIn(code, str(list(AccountActivity.objects.values())))
        self.assertNotIn("OwnerChooses7!", str(list(AccountActivity.objects.values())))

    def test_five_wrong_codes_persist_across_clients(self):
        link, code = self.delivery()
        for _ in range(5):
            Client().post(link, {"code": "invalid"})
        row = PasswordResetCode.objects.get()
        self.assertEqual(row.attempts, 5); self.assertTrue(row.used)
        self.assertContains(Client().post(link, {"code": code}), "already used")

    def test_expired_changed_email_and_disabled_accounts_fail(self):
        link, code = self.delivery()
        self.local.email = "changed@example.com"; self.local.save()
        self.assertNotContains(Client().post(link, {"code": code}), "New Password")
        self.local.email = "local@example.com"; self.local.is_active = False; self.local.save()
        self.assertContains(Client().post(link, {"code": code}), "invalid")
        self.local.is_active = True; self.local.save()
        PasswordResetCode.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertContains(Client().post(link, {"code": code}), "expired")

    def test_public_mobile_cannot_use_username_or_email_verification_code(self):
        for purpose in ("username", "email_verification"):
            PasswordResetCode.objects.all().delete()
            _, code = self.delivery(purpose)
            response = self.client.post(reverse("mobile_password_reset_confirm"), json.dumps({
                "email": self.local.email, "code": code, "new_password": "OwnerChooses7!", "confirm_password": "OwnerChooses7!"}), content_type="application/json")
            self.assertEqual(response.status_code, 400)

    def test_scope_denies_foreign_recovery_and_verification(self):
        for account in (self.other, self.foreign, self.super, self.actor):
            for action in ("assist_recovery", "verify_email"):
                self.assertEqual(self.request_recovery(account=account, action=action).status_code, 403)
        self.actor.major = None; self.actor.save()
        self.assertEqual(self.request_recovery().status_code, 403)

    def test_super_admin_global_recovery_and_facility_admin_denied(self):
        self.client.force_login(self.super)
        self.foreign.email_verified = True; self.foreign.save()
        self.delivery(account=self.foreign)
        from .role_permissions import sync_user_admin_permissions
        facility = User.objects.create_user(username="facility-support", role="Facilities Admin")
        sync_user_admin_permissions(facility); self.client.force_login(facility)
        self.assertEqual(self.request_recovery().status_code, 403)

    def test_seller_suspend_restore_keeps_account_active_and_approval(self):
        seller = SellerRequest.objects.create(student_id=self.local.username, full_name="Local Student", status="approved", reviewed_at=timezone.now())
        date = seller.reviewed_at
        def action(status):
            return self.client.post(reverse("admin_users_action"), {"action":"seller_access", "account_ref":f"mobile:{self.local.pk}", "seller_status":status})
        self.assertEqual(action("suspended").status_code, 302)
        seller.refresh_from_db(); self.local.refresh_from_db()
        self.assertTrue(seller.is_suspended); self.assertTrue(self.local.is_active)
        self.assertEqual(seller.status, "approved")
        self.assertEqual(action("approved").status_code, 302)
        seller.refresh_from_db(); self.assertFalse(seller.is_suspended); self.assertEqual(seller.reviewed_at, date)
        self.assertEqual(action("rejected").status_code, 403)

    def test_foreign_seller_and_account_mutations_denied(self):
        for account in (self.other, self.foreign):
            response = self.client.post(reverse("admin_users_action"), {"action":"seller_access", "account_ref":f"mobile:{account.pk}", "seller_status":"suspended"})
            self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(reverse("admin_users_action"), {"action":"deactivate", "account_ref":f"mobile:{self.local.pk}"}).status_code, 403)

    def test_ambiguous_seller_identity_cannot_modify_foreign_application(self):
        self.other.student_id=self.local.username; self.other.save()
        seller=SellerRequest.objects.create(student_id=self.local.username,full_name="Ambiguous identity",status="approved")
        response=self.client.post(reverse("admin_users_action"),{"action":"seller_access","account_ref":f"mobile:{self.local.pk}","seller_status":"suspended"})
        self.assertEqual(response.status_code,403)
        seller.refresh_from_db(); self.assertFalse(seller.is_suspended)

    def test_resend_invalidates_previous_code_and_rate_limits(self):
        link, code = self.delivery()
        with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True) as sender:
            self.request_recovery(); self.assertFalse(sender.called)
        PasswordResetCode.objects.update(created_at=timezone.now()-timedelta(minutes=2))
        new_link, new_code = self.delivery()
        self.assertContains(Client().post(link, {"code":code}), "already used")
        self.assertEqual(Client().post(new_link, {"code":new_code}).status_code, 302)

    def test_csrf_and_tampered_link(self):
        link, code = self.delivery()
        self.assertEqual(Client(enforce_csrf_checks=True).post(link, {"code":code}).status_code, 403)
        self.assertContains(Client().get(link.rstrip('/')+'x/'), "invalid")
        self.assertEqual(Client().get(link)["Cache-Control"].find("no-store") >= 0, True)

    @override_settings(CAMPUSHUB_PUBLIC_BASE_URL="https://campushub.example")
    @patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True)
    def test_email_origin_does_not_trust_request_host(self, sender):
        self.client.post(reverse("mobile_password_reset"), json.dumps({"email": self.local.email}), content_type="application/json", HTTP_HOST="untrusted.example")
        self.assertNotIn("link", sender.call_args.kwargs)

    def test_email_change_clears_verification_and_manual_password_edit_is_rejected(self):
        self.client.force_login(self.super)
        payload = {"account_ref":f"mobile:{self.local.pk}", "first_name":"Local", "last_name":"Student",
            "username":self.local.username, "email":"new-owner@example.com", "account_type":"student", "role":"User",
            "department":self.btled.pk, "major":self.he.pk, "is_active":"on"}
        previous = self.local.password_hash
        response = self.client.post(reverse("admin_users_save"), {**payload, "password":"AdminChooses7!", "confirm_password":"AdminChooses7!"})
        self.assertEqual(response.status_code, 302)
        self.local.refresh_from_db(); self.assertEqual(self.local.password_hash, previous)
        self.assertEqual(self.local.email, "local@example.com")
        self.client.post(reverse("admin_users_save"), payload)
        self.local.refresh_from_db(); self.assertFalse(self.local.email_verified)
        self.assertEqual(self.local.email, "new-owner@example.com")

    def test_super_deactivation_preserves_history_and_reactivation(self):
        self.client.force_login(self.super)
        seller = SellerRequest.objects.create(student_id=self.local.username, full_name="Local Student", status="approved")
        ref = f"mobile:{self.local.pk}"
        for action, active in (("deactivate",False),("activate",True)):
            self.client.post(reverse("admin_users_action"), {"action":action,"account_ref":ref})
            self.local.refresh_from_db(); self.assertEqual(self.local.is_active, active)
            self.assertTrue(SellerRequest.objects.filter(pk=seller.pk).exists())
        self.assertTrue(AccountActivity.objects.filter(account_ref=ref,activity_type="ACCOUNT_DEACTIVATED").exists())
        self.assertTrue(AccountActivity.objects.filter(account_ref=ref,activity_type="ACCOUNT_REACTIVATED").exists())

    @patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True)
    def test_existing_mobile_request_verify_confirm_contract(self, sender):
        self.local.email_verified=True; self.local.save()
        payload={"email":self.local.email}
        response=self.client.post(reverse("mobile_password_reset"),json.dumps(payload),content_type="application/json")
        self.assertEqual(response.status_code,200); self.assertEqual(response.json()["step"],2)
        self.assertEqual(self.client.post(reverse("mobile_password_reset"),json.dumps(payload),content_type="application/json").status_code,429)
        code=sender.call_args.kwargs["code"]
        response=self.client.post(reverse("mobile_password_reset_verify"),json.dumps({**payload,"code":code}),content_type="application/json")
        self.assertEqual(response.status_code,200)
        response=self.client.post(reverse("mobile_password_reset_confirm"),json.dumps({**payload,"recovery_grant":response.json()["recovery_grant"],"new_password":"OwnerChooses7!","confirm_password":"OwnerChooses7!"}),content_type="application/json")
        self.assertEqual(response.status_code,200)
        self.local.refresh_from_db(); self.assertTrue(self.local.email_verified)

    @patch("modules.notifications.services.email_service.send_account_recovery_email", side_effect=RuntimeError("private SMTP details"))
    def test_mobile_failed_email_has_no_usable_code_or_internal_error(self, sender):
        response=self.client.post(reverse("mobile_password_reset"),json.dumps({"email":self.local.email}),content_type="application/json")
        self.assertEqual(response.status_code,503)
        self.assertNotIn("private SMTP details",response.content.decode())
        self.assertTrue(PasswordResetCode.objects.get().used)

    def test_export_browser_fixtures(self):
        if not os.environ.get("RECOVERY_REVIEW_DIR"):
            return
        folder = Path(os.environ["RECOVERY_REVIEW_DIR"]); folder.mkdir(parents=True, exist_ok=True)
        (folder/"self-service.html").write_bytes(Client().get(reverse("account_recovery_start")).content)
        for name, actor in (("marketplace",self.actor),("super",self.super)):
            self.client.force_login(actor)
            (folder/f"{name}.html").write_bytes(self.client.get(reverse("admin_users_page")).content)
        self.client.force_login(self.actor)
        self.local.email_verified=False; self.local.contact_number="09817149863"; self.local.save()
        (folder/"unverified.html").write_bytes(self.client.get(reverse("admin_users_page")).content)
        link, code = self.delivery("email_verification")
        (folder/"owner.html").write_bytes(Client().get(link).content)
