"""Administrator exclusion and owner recovery, using isolated records and mocked email."""
import json
from unittest.mock import patch

from django.contrib.auth.models import Group, Permission
from django.db import connection
from django.test import TestCase, Client
from django.urls import reverse

from api.models import CampusHubUser, PasswordResetCode, SellerRequest
from .models import AccountActivity, Role, User
from .recovery_codes import send_code, RecoveryError
from .support_scope import is_administrator_account, can_view_recovery_info
from .test_marketplace_support import MarketplaceSupportTests
from .user_management import build_account_rows


class RecoveryEligibilityTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    setUp = MarketplaceSupportTests.setUp

    def assist(self, target, action="assist_recovery"):
        return self.client.post(reverse("admin_users_action"), {"account_ref":
            f"{'admin' if isinstance(target, User) else 'mobile'}:{target.pk}", "action": action,
            "confirm_reset": "1", "recovery_purpose": "password"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def api(self, name, payload):
        return Client().post(reverse(name), json.dumps(payload), content_type="application/json")

    def admin_targets(self):
        targets = [self.super, self.actor]
        for name in ("Facilities Admin", "Empty Custom Admin", "Retired Custom Admin", "Unknown Admin"):
            if "Custom" in name:
                Role.objects.create(role_name=name, is_active="Retired" not in name)
            targets.append(User.objects.create_user(username=name.replace(" ", "-"), role=name,
                email=name.replace(" ", "-") + "@example.com", email_verified=True))
        targets.append(User.objects.create_user(username="staff-only", role="User", is_staff=True))
        targets.append(User.objects.create_user(username="flag-only", role="User", is_superuser=True))
        direct = User.objects.create_user(username="direct-access", role="User")
        direct.user_permissions.add(Permission.objects.get(codename="can_manage_admin_accounts"))
        targets.append(direct)
        grouped = User.objects.create_user(username="group-access", role="User")
        group = Group.objects.create(name="Existing admin authority")
        group.permissions.add(Permission.objects.get(codename="can_view_users"))
        grouped.groups.add(group); targets.append(grouped)
        targets.append(CampusHubUser.objects.create(username="legacy-admin-type", email="legacy-admin@example.com", user_type="admin", role="User"))
        targets.append(CampusHubUser.objects.create(username="mobile-custom-role", email="mobile-custom@example.com", user_type="student", role="Custom Admin"))
        return targets

    def test_all_administrator_sources_rejected_by_ui_and_every_action_alias(self):
        targets = self.admin_targets(); self.client.force_login(self.super)
        rows = {row["username"]: row for row in build_account_rows(self.super)}
        with patch("modules.notifications.services.email_service.send_account_recovery_email") as mail:
            for target in targets:
                with self.subTest(target=target.username):
                    source = "admin" if isinstance(target, User) else "mobile"
                    self.assertTrue(is_administrator_account(source, target))
                    row = rows[target.username]
                    self.assertTrue(row["is_administrator"])
                    self.assertEqual(row["recovery_method"], "Verified Email")
                    for flag in ("can_assist_recovery", "can_reset", "can_recover", "can_verify_email", "can_manage_seller"):
                        self.assertFalse(row[flag])
                    for action in ("assist_recovery", "reset_password", "verify_email"):
                        self.assertEqual(self.assist(target, action).status_code, 403)
            mail.assert_not_called()
        self.assertFalse(PasswordResetCode.objects.exists())
        self.assertFalse(AccountActivity.objects.filter(activity_type__contains="RECOVERY").exists())

    def test_super_menu_keeps_three_dots_and_contextual_admin_actions(self):
        self.client.force_login(self.super)
        for target in (self.super, self.actor, User.objects.create_user(username="menu-facilities", role="Facilities Admin")):
            response = self.client.get(reverse("admin_users_page"), {"q": target.username})
            self.assertNotContains(response, 'class="dropdown-item assist-recovery"')
            self.assertContains(response, 'more-action')
            self.assertContains(response, "View Activity")
            if target == self.super:
                self.assertNotContains(response, "Manage Role</button>")
                self.assertNotContains(response, "Deactivate Account</button>")
            else:
                self.assertContains(response, "Manage Role</button>")
            if target.role == "Marketplace Admin":
                self.assertContains(response, "Manage Program/Major Scope</button>")
            else:
                self.assertNotContains(response, "Manage Program/Major Scope</button>")

    def test_super_assists_students_guests_sellers_and_ordinary_django_users_globally(self):
        guest = CampusHubUser.objects.create(username="guest-owner", user_type="guest", email="guest@example.com", email_verified=True)
        SellerRequest.objects.create(student_id=self.local.username, full_name="Student Seller", status="approved")
        ordinary = User.objects.create_user(username="ordinary-django-owner", role="User", email="ordinary@example.com", email_verified=True)
        self.foreign.email_verified = True; self.foreign.save()
        self.client.force_login(self.super)
        rows = {row["username"]: row for row in build_account_rows(self.super)}
        with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True):
            for target in (self.local, self.foreign, guest, ordinary):
                with self.subTest(target=target.username):
                    self.assertFalse(rows[target.username]["is_administrator"])
                    self.assertTrue(rows[target.username]["can_assist_recovery"])
                    self.assertEqual(self.assist(target).status_code, 403)
        self.assertEqual(AccountActivity.objects.filter(activity_type="ACCOUNT_RECOVERY_INITIATED").count(), 0)
        self.assertEqual(AccountActivity.objects.filter(activity_type="ACCOUNT_RECOVERY_CODE_SENT").count(), 0)

    def test_marketplace_scope_matches_program_and_btled_major_and_excludes_admins(self):
        self.assertTrue(can_view_recovery_info(self.actor, "mobile", self.local))
        self.assertFalse(can_view_recovery_info(self.actor, "mobile", self.other))
        self.assertFalse(can_view_recovery_info(self.actor, "mobile", self.foreign))
        self.assertEqual(self.assist(self.actor).status_code, 403)
        self.actor.major = None; self.actor.save()
        self.assertFalse(can_view_recovery_info(self.actor, "mobile", self.local))
        self.actor.department = self.bfpt; self.actor.save()
        self.assertTrue(can_view_recovery_info(self.actor, "mobile", self.foreign))
        self.assertFalse(can_view_recovery_info(self.actor, "mobile", self.local))

    def test_facilities_actor_denied_even_with_old_direct_recovery_grant(self):
        facility = User.objects.create_user(username="old-facility-grant", role="Facilities Admin", is_staff=True)
        facility.user_permissions.add(Permission.objects.get(codename="can_reset_user_password"))
        self.client.force_login(facility)
        self.assertFalse(can_view_recovery_info(facility, "mobile", self.local))
        self.assertFalse(any(row["can_assist_recovery"] for row in build_account_rows(facility)))
        self.assertEqual(self.assist(self.local).status_code, 403)

    def test_service_boundary_denies_admin_without_creating_code(self):
        from django.test import RequestFactory
        request = RequestFactory().post("/admin-users/action/"); request.user = self.super
        with self.assertRaises(RecoveryError) as failure:
            send_code(request, "admin", self.actor, "password", assisted=True)
        self.assertEqual(failure.exception.status, 403)
        self.assertFalse(PasswordResetCode.objects.exists())

    def test_each_builtin_admin_self_service_uses_existing_api_and_audit_events(self):
        facility = User.objects.create_user(username="owner-facilities", role="Facilities Admin")
        for target in (self.super, self.actor, facility):
            with self.subTest(role=target.role):
                target.email = target.username + "@example.com"; target.email_verified = True; target.save()
                with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True) as mail:
                    response = self.api("mobile_password_reset", {"email": target.email})
                    self.assertEqual(response.status_code, 200)
                    code = mail.call_args.kwargs["code"]
                verified = self.api("mobile_password_reset_verify", {"email": target.email, "code": code})
                self.assertEqual(verified.status_code, 200)
                response = self.api("mobile_password_reset_confirm", {"email": target.email,
                    "recovery_grant": verified.json()["recovery_grant"], "new_password": "OwnerChooses7!", "confirm_password": "OwnerChooses7!"})
                self.assertEqual(response.status_code, 200)
                target.refresh_from_db(); self.assertTrue(target.check_password("OwnerChooses7!"))
                events = AccountActivity.objects.filter(account_ref=f"admin:{target.pk}")
                self.assertTrue(events.filter(activity_type="SELF_SERVICE_RECOVERY_INITIATED").exists())
                self.assertTrue(events.filter(activity_type="PASSWORD_RESET_COMPLETED").exists())
                self.assertNotIn(code, str(list(events.values("metadata", "activity"))))
                self.assertNotIn("OwnerChooses7!", str(list(events.values("metadata", "activity"))))

    def test_web_login_links_to_code_only_owner_page_and_get_only(self):
        response = Client().get(reverse("admin_login_page"))
        self.assertContains(response, f'href="{reverse("account_recovery_start")}"')
        self.assertContains(response, "Forgot Username or Password?")
        response = Client().get(reverse("account_recovery_start"))
        self.assertContains(response, 'class="code-boxes"')
        self.assertContains(response, reverse("mobile_password_reset_verify"))
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(Client().post(reverse("account_recovery_start")).status_code, 405)
