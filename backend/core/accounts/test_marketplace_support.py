"""Real permission/scope and reset flow tests on isolated records only."""
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.hashers import make_password, check_password
from django.db import connection
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from api.models import CampusHubUser, PasswordResetCode, SellerRequest, Product
from .models import AccountActivity, Department, ProgramMajor, Role, User
from .role_permissions import BUILTIN_ROLE_PERMISSIONS, set_role_permissions, sync_user_admin_permissions


@override_settings(CAMPUSHUB_PUBLIC_BASE_URL="https://campushub.example")
class MarketplaceSupportTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.bfpt = Department.objects.get(code="BFPT")
        self.btled = Department.objects.get(code="BTLED")
        self.he = ProgramMajor.objects.get(program=self.btled, code="HE")
        self.ia = ProgramMajor.objects.get(program=self.btled, code="IA")
        for name, grants in BUILTIN_ROLE_PERMISSIONS.items():
            role = Role.objects.get_or_create(role_name=name)[0]
            set_role_permissions(role, list(grants))
        self.actor = User.objects.create_user(username="support-admin", role="Marketplace Admin", department=self.btled, major=self.he)
        sync_user_admin_permissions(self.actor)
        self.super = User.objects.create_superuser(username="support-super", role="Super Admin", email="super@example.com")
        self.local = CampusHubUser.objects.create(username="local-student", email="local@example.com", user_type="student",
            department=self.btled, major=self.he, email_verified=True, password_hash=make_password("OriginalCampus7!"))
        self.other = CampusHubUser.objects.create(username="other-major", email="other@example.com", user_type="student",
            department=self.btled, major=self.ia, password_hash="unused")
        self.foreign = CampusHubUser.objects.create(username="other-program", email="foreign@example.com", user_type="student", department=self.bfpt)
        self.client.force_login(self.actor)

    def reset(self, ref=None, **extra):
        return self.client.post(reverse("admin_users_action"), {"action": "reset_password",
            "confirm_reset": "1", "account_ref": ref or f"mobile:{self.local.pk}", **extra})

    def event(self, account=None, module="Products", kind="PRODUCT_APPROVED", text="Scoped product approved"):
        account = account or self.local
        return AccountActivity.objects.create(account_ref=f"mobile:{account.pk}", account_source="mobile",
            account_id=account.pk, activity_type=kind, activity=text, module=module, result="success",
            ip_address="192.0.2.9", user_agent="private-device")

    def test_sidebar_and_permissions(self):
        response = self.client.get(reverse("admin_users_page"))
        self.assertEqual(response.status_code, 200)
        for route in ("admin_products_page", "admin_orders_page", "admin_sellers_page", "admin_user_monitoring_page", "admin_generate_reports_page", "admin_settings_page"):
            self.assertContains(response, reverse(route))
        for route in ("admin_roles_page", "admin_backup_page", "admin_facility_page"):
            self.assertNotContains(response, f'href="{reverse(route)}')
        self.assertContains(response, "Generate Reports")
        self.assertNotContains(response, "Add Admin")
        self.assertNotContains(response, "Manage Role</button>")
        self.assertContains(response, 'class="dropdown-item assist-recovery"')
        self.assertNotContains(response, 'id="resetNewPassword"')
        for code in ("can_view_users", "can_reset_user_password", "can_view_user_monitoring"):
            self.assertTrue(self.actor.has_perm("accounts." + code))
        for code in ("can_manage_admin_accounts", "can_manage_roles_permissions", "can_system_backup", "can_manage_facilities"):
            self.assertFalse(self.actor.has_perm("accounts." + code))

    def test_rows_counts_and_embedded_json_are_scoped(self):
        hidden = User.objects.create_user(username="same-major-admin", role="Facilities Admin", department=self.btled, major=self.he)
        response = self.client.get(reverse("admin_users_page"), {"department": self.bfpt.pk})
        self.assertEqual(response.context["total_users"], 1)
        self.assertEqual(response.context["users"], [])
        response = self.client.get(reverse("admin_users_page"))
        self.assertEqual([row["ref"] for row in response.context["users"]], [f"mobile:{self.local.pk}"])
        self.assertNotContains(response, self.other.email)
        self.assertNotContains(response, hidden.username)
        self.assertNotContains(response, "password_hash")
        self.actor.major = None; self.actor.save(update_fields=["major"])
        self.assertEqual(self.client.get(reverse("admin_users_page")).context["total_users"], 0)

    def test_bfpt_and_super_scope(self):
        self.actor.department = self.bfpt; self.actor.major = None; self.actor.save()
        self.assertEqual(self.client.get(reverse("admin_users_page")).context["users"][0]["username"], self.foreign.username)
        self.client.force_login(self.super)
        usernames = {row["username"] for row in self.client.get(reverse("admin_users_page")).context["users"]}
        self.assertTrue({self.local.username, self.other.username, self.actor.username, self.super.username}.issubset(usernames))

    def test_forged_actions_and_foreign_resets_are_denied(self):
        for action in ("activate", "deactivate"):
            response = self.client.post(reverse("admin_users_action"), {"action": action, "account_ref": f"mobile:{self.local.pk}"})
            self.assertEqual(response.status_code, 403)
        for ref in (f"mobile:{self.other.pk}", f"admin:{self.super.pk}", f"admin:{self.actor.pk}"):
            self.assertEqual(self.reset(ref).status_code, 403)
        self.assertNotEqual(self.client.post(reverse("admin_users_save"), {"role": "Super Admin"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin_roles_page")).status_code, 403)
        self.assertEqual(self.client.post(reverse("admin_roles_save"), {"role_name": "Malicious"}).status_code, 403)
        self.assertFalse(Role.objects.filter(role_name="Malicious").exists())

    @patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True)
    def test_mobile_reset_delivers_hashed_code_not_admin_password(self, delivery):
        previous = self.local.password_hash
        self.assertEqual(self.reset(password="AdminChooses7!", confirm_password="AdminChooses7!").status_code, 403)
        delivery.assert_not_called()
        self.client.post(reverse("mobile_password_reset"), json.dumps({"email": self.local.email}), content_type="application/json")
        self.local.refresh_from_db(); self.assertEqual(self.local.password_hash, previous)
        code = delivery.call_args.kwargs["code"]
        reset = PasswordResetCode.objects.get(email=self.local.email)
        self.assertNotEqual(reset.code_hash, code); self.assertTrue(check_password(code, reset.code_hash))
        self.assertNotIn(code, str(list(AccountActivity.objects.values())))
        self.reset(); self.assertEqual(delivery.call_count, 1)
        proof = self.client.post(reverse("mobile_password_reset_verify"), json.dumps({"email": self.local.email, "code": code}), content_type="application/json")
        self.assertEqual(proof.status_code, 200)
        response = self.client.post(reverse("mobile_password_reset_confirm"), json.dumps({"email": self.local.email,
            "recovery_grant": proof.json()["recovery_grant"], "new_password": "OwnerChooses7!", "confirm_password": "OwnerChooses7!"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.local.refresh_from_db(); self.assertTrue(check_password("OwnerChooses7!", self.local.password_hash))
        self.assertEqual(self.client.post(reverse("mobile_password_reset_verify"), json.dumps({"email": self.local.email, "code": code}), content_type="application/json").status_code, 400)

    @patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=False)
    def test_delivery_failure_does_not_change_password_or_leave_usable_code(self, delivery):
        previous = self.local.password_hash
        response = self.client.post(reverse("mobile_password_reset"), json.dumps({"email": self.local.email}), content_type="application/json")
        self.assertEqual(response.status_code, 503)
        self.local.refresh_from_db(); self.assertEqual(self.local.password_hash, previous)
        self.assertTrue(PasswordResetCode.objects.get(email=self.local.email).used)
        self.assertEqual(AccountActivity.objects.get(activity_type="ACCOUNT_RECOVERY_DELIVERY_FAILED").result, "failed")

    @patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True)
    def test_confirmation_and_disabled_or_ambiguous_targets(self, delivery):
        self.reset(confirm_reset=""); self.assertFalse(delivery.called)
        self.local.is_active = False; self.local.save(); self.reset(); self.assertFalse(delivery.called)
        self.local.is_active = True; self.local.save()
        CampusHubUser.objects.create(username="duplicate-email", email=self.local.email.upper(), user_type="guest")
        self.reset(); self.assertFalse(delivery.called)

    @patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True)
    def test_django_owner_link_expiry_replay_validation_and_csrf(self, delivery):
        from urllib.parse import urlsplit
        from datetime import timedelta
        self.super.email_verified = True; self.super.set_password("OriginalCampus7!"); self.super.save()
        self.client.post(reverse("mobile_password_reset"), json.dumps({"email": self.super.email}), content_type="application/json")
        from django.core import signing
        self.assertNotIn("link", delivery.call_args.kwargs)
        link = reverse("account_recovery", kwargs={"token": signing.dumps(PasswordResetCode.objects.latest("pk").pk, salt="campushub-account-recovery")})
        code = delivery.call_args.kwargs["code"]
        owner = Client()
        self.assertContains(owner.get(link), "Verification Code")
        self.assertNotContains(owner.get(link), 'name="new_password"')
        self.assertEqual(Client(enforce_csrf_checks=True).post(link, {"code": code}).status_code, 403)
        owner.post(link, {"code": code})
        self.assertContains(owner.get(link), "New Password")
        self.assertContains(owner.post(link, {"new_password": "short", "confirm_password": "short"}), "at least 8 characters")
        response = owner.post(link, {"new_password": "OwnerChooses7!", "confirm_password": "OwnerChooses7!"})
        self.assertContains(response, "Password updated")
        self.super.refresh_from_db(); self.assertTrue(self.super.check_password("OwnerChooses7!"))
        self.assertContains(owner.get(link), "already used")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        PasswordResetCode.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertContains(Client().get(link), "expired")

    def test_monitoring_all_sources_and_history_exclude_sensitive_events(self):
        self.event()
        self.event(self.other, text="Foreign program record")
        self.event(module="System Backup", text="Confidential backup")
        self.event(module="Authentication", kind="login_failed", text="Sensitive security")
        self.event(module="Facilities", text="Facility only")
        self.event(module="Roles & Permissions", text="Role changes")
        response = self.client.get(reverse("admin_user_monitoring_page"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["marketplace_activity_count"], 1)
        self.assertEqual(response.context["users_json"][0]["lastActivity"], "Product Approved")
        self.assertEqual(response.context["users_json"][0]["ip"], "")
        self.assertEqual(response.context["users_json"][0]["sessions"], [])
        for text in ("Foreign program record", "Confidential backup", "Sensitive security", "Facility only", "Role changes", "private-device", "192.0.2.9"):
            self.assertNotContains(response, text)
        self.assertEqual(self.client.get(reverse("admin_user_monitoring_page"), {"account_ref": f"mobile:{self.other.pk}"}).status_code, 404)
        users = self.client.get(reverse("admin_users_page"))
        self.assertEqual(users.context["users"][0]["activities"][0]["activity"], "Scoped product approved")
        self.assertEqual(len(users.context["users"][0]["activities"]), 1)

    def test_facilities_scope_is_not_changed_and_super_monitoring_is_unrestricted(self):
        facilities = User.objects.create_user(username="global-facilities", role="Facilities Admin")
        sync_user_admin_permissions(facilities)
        self.assertTrue(facilities.has_perm("accounts.can_manage_facilities"))
        self.assertFalse(facilities.has_perm("accounts.can_view_users"))
        self.assertFalse(facilities.has_perm("accounts.can_view_user_monitoring"))
        self.event(self.other, module="System Backup", text="Super-only event")
        self.client.force_login(self.super)
        self.assertContains(self.client.get(reverse("admin_user_monitoring_page")), "Super-only event")

    def test_mobile_seller_applications_are_scoped_and_logged(self):
        local = SellerRequest.objects.create(student_id=self.local.username, full_name="Local Seller", product_type="Supplies")
        foreign = SellerRequest.objects.create(student_id=self.other.username, full_name="Other Seller", product_type="Supplies")
        response = self.client.get(reverse("marketplace_seller_requests"))
        self.assertEqual([row["id"] for row in response.json()["seller_requests"]], [local.pk])
        self.assertEqual(self.client.post(reverse("marketplace_approve_seller_request", args=[foreign.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("marketplace_approve_seller_request", args=[local.pk])).status_code, 302)
        local.refresh_from_db(); self.assertEqual(local.status, "approved")
        event = AccountActivity.objects.get(activity_type="SELLER_APPROVED")
        self.assertEqual(event.account_ref, f"mobile:{self.local.pk}")
        self.assertEqual(event.metadata["actor_admin_id"], self.actor.pk)
        self.assertEqual(self.client.get(reverse("admin_user_monitoring_page")).context["marketplace_activity_count"], 1)

    def test_scoped_django_seller_product_actions_are_logged(self):
        seller = User.objects.create_user(username="ordinary-he-seller", role="User", department=self.btled, major=self.he)
        product = Product.objects.create(seller=seller, name="Scoped Product", department=self.btled, major=self.he, price=10)
        self.assertEqual(self.client.post(reverse("marketplace_approve_product", args=[product.pk])).status_code, 302)
        self.assertEqual(AccountActivity.objects.get(activity_type="PRODUCT_APPROVED").account_ref, f"admin:{seller.pk}")
        self.assertContains(self.client.get(reverse("admin_user_monitoring_page")), "Scoped Product")
        # Explicit product scope overrides its owner's affiliation, just as Products does.
        foreign = Product.objects.create(seller=seller, name="Foreign Product", department=self.bfpt, price=10)
        self.client.force_login(self.super)
        self.client.post(reverse("marketplace_approve_product", args=[foreign.pk]))
        self.client.force_login(self.actor)
        self.assertNotContains(self.client.get(reverse("admin_user_monitoring_page")), "Foreign Product")

    @patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True)
    def test_expired_and_exhausted_codes_are_rejected(self, delivery):
        from datetime import timedelta
        self.client.post(reverse("mobile_password_reset"), json.dumps({"email": self.local.email}), content_type="application/json")
        code = delivery.call_args.kwargs["code"]
        reset = PasswordResetCode.objects.get(email=self.local.email)
        reset.expires_at = timezone.now() - timedelta(seconds=1); reset.save()
        payload = {"email": self.local.email, "code": code}
        self.assertEqual(self.client.post(reverse("mobile_password_reset_verify"), json.dumps(payload), content_type="application/json").status_code, 400)
        reset.expires_at = timezone.now() + timedelta(minutes=15); reset.save()
        for _ in range(5):
            self.assertEqual(self.client.post(reverse("mobile_password_reset_verify"), json.dumps({**payload, "code": "invalid"}), content_type="application/json").status_code, 400)
        # Wrong six-digit guesses count; malformed input is rejected before checking a code.
        wrong = "999999" if code != "999999" else "888888"
        for _ in range(5):
            self.assertEqual(self.client.post(reverse("mobile_password_reset_verify"), json.dumps({**payload, "code": wrong}), content_type="application/json").status_code, 400)
        reset.refresh_from_db(); self.assertTrue(reset.used)
        self.assertEqual(self.client.post(reverse("mobile_password_reset_verify"), json.dumps(payload), content_type="application/json").status_code, 400)

    def test_export_browser_fixture(self):
        if not os.environ.get("SUPPORT_REVIEW_DIR"):
            return
        self.event()
        folder = Path(os.environ["SUPPORT_REVIEW_DIR"]); folder.mkdir(parents=True, exist_ok=True)
        for name, route in (("support-users", "admin_users_page"), ("support-monitoring", "admin_user_monitoring_page")):
            (folder / f"{name}.html").write_bytes(self.client.get(reverse(route)).content)
