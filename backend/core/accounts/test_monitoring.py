"""Real monitoring behavior tested against the isolated Django test database."""
import json
import os
import re
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.activity_logging import log_account_activity
from accounts.models import AccountActivity, AdminTabToken, Role, User
from accounts.monitoring import event_rows, presence_age
from api.models import CampusHubUser, Product


class MonitoringRefinementTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.admin = User.objects.create_superuser(username="monitor-owner", email="owner@example.com", password="Example123!", role="Super Admin")
        self.student = CampusHubUser.objects.create(username="monitor-student", email="student@example.com", first_name="Student", last_name="Example", role="User", user_type="student", password_hash="unused")
        self.guest = CampusHubUser.objects.create(username="monitor-guest", email="guest@example.com", role="Standard User", user_type="guest", password_hash="unused")
        self.client.force_login(self.admin)
        self.url = reverse("admin_user_monitoring_page")

    def event(self, account=None, **fields):
        account = account or self.student
        source = "admin" if isinstance(account, User) else "mobile"
        defaults = dict(account_source=source, account_id=account.pk, account_ref=f"{source}:{account.pk}",
                        username=account.username, full_name="Student Example" if source == "mobile" else account.username,
                        account_type="admin" if source == "admin" else account.user_type,
                        role=account.role, activity_type="login_success", activity="Logged in", module="Authentication", result="success")
        defaults.update(fields)
        return AccountActivity.objects.create(**defaults)

    def token(self, key, **fields):
        defaults = dict(user=self.admin, last_seen_at=self.now, expires_at=self.now + timedelta(hours=1))
        defaults.update(fields)
        return AdminTabToken.objects.create(key=key, **defaults)

    def test_real_counts_presence_and_user_labels(self):
        self.token("private-admin-token", last_seen_at=self.now - timedelta(minutes=3))
        self.event()
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_active_users"], 3)
        self.assertEqual(response.context["online_now"], 2)
        self.assertEqual(response.context["active_sessions"], 1)
        self.assertContains(response, "Active Accounts")
        self.assertContains(response, "Enabled user accounts")
        self.assertContains(response, "Active Web Sessions")
        self.assertContains(response, "Currently authenticated web sessions")
        self.assertContains(response, "Last Seen")
        self.assertContains(response, "3 min ago")
        self.assertNotContains(response, "Standard User")
        self.assertNotContains(response, "private-admin-token")
        self.assertNotContains(response, 'id="peakPeriod"')
        self.assertEqual({row["role_label"] for row in response.context["users"]}, {"User", "Super Admin"})

    def test_sessions_exclude_expired_disabled_stale_missing_and_future_presence(self):
        self.token("usable")
        self.token("expired", expires_at=self.now - timedelta(seconds=1))
        self.token("not-observed", last_seen_at=None)
        self.token("remembered-stale", last_seen_at=self.now - timedelta(days=2), expires_at=self.now + timedelta(days=20))
        self.token("future", last_seen_at=self.now + timedelta(hours=1))
        self.token("")
        disabled = User.objects.create_user(username="disabled-monitor", is_active=False)
        self.token("disabled", user=disabled)
        suspended = User.objects.create_user(username="suspended-monitor", is_suspended=True)
        self.token("suspended", user=suspended)
        response = self.client.get(self.url)
        self.assertEqual(response.context["active_sessions"], 1)
        sessions = next(row["sessions"] for row in response.context["users_json"] if row["ref"] == f"admin:{self.admin.pk}")
        self.assertContains(response, "No failed login attempts in selected period.")
        self.assertEqual(len(sessions), 1)
        self.assertSetEqual(set(sessions[0]), {"created", "last_seen", "expires", "active"})
        self.assertEqual(response.context["total_active_users"], 3)

    def test_disabled_and_logged_out_mobile_users_are_not_online(self):
        self.event()
        self.event(activity_type="logout", activity="Logged out")
        self.guest.is_active = False
        self.guest.save(update_fields=["is_active"])
        self.event(self.guest)
        response = self.client.get(self.url)
        self.assertEqual(response.context["online_now"], 0)
        self.assertContains(response, "No users are online right now.")

    def test_presence_age_is_presence_not_audit_action(self):
        self.assertEqual(presence_age(self.now - timedelta(seconds=5), self.now), "Active now")
        self.assertEqual(presence_age(self.now - timedelta(seconds=40), self.now), "Just now")
        self.assertEqual(presence_age(self.now - timedelta(seconds=75), self.now), "1 min ago")
        self.event()
        self.event(activity_type="PRODUCT_APPROVED", activity="Reviewed a product", module="Marketplace")
        response = self.client.get(self.url)
        self.assertEqual(response.context["online_users"][0]["online_activity"], "Active now")
        self.assertEqual(response.context["users"][0]["last_activity"], "Product Approved")

    def test_final_log_columns_keep_target_in_details_only(self):
        role = Role.objects.create(role_name="Affected Test Role")
        event = self.event(self.admin, module="Roles & Permissions", activity_type="ROLE_DEACTIVATED",
            activity="Role Deactivated: Affected Test Role by monitor-owner",
            metadata={"actor_admin_id": self.admin.pk, "role_id": str(role.pk)})
        response = self.client.get(self.url)
        table = response.content.decode().split('<table class="recent-activity-table">', 1)[1].split('</table>', 1)[0]
        self.assertEqual(re.findall(r"<th>(.*?)</th>", table), ["Time", "User", "Action", "Module", "Result", "Actions"])
        self.assertNotIn(role.role_name, table)
        self.assertIn("monitor-owner", table)
        self.assertEqual(table.count('class="monitor-view js-activity-view"'), 1)
        self.assertEqual(response.context["recent_activities"][0]["detail"]["affected_record"]["name"], role.role_name)
        self.assertEqual(AccountActivity.objects.get(pk=event.pk).activity, event.activity)
        empty = self.client.get(self.url, {"q": "no-such-test-account"}).content.decode()
        self.assertIn('colspan="6" class="monitor-no-data">No activities', empty)

    def test_last_activity_is_action_only_without_rewriting_audit_history(self):
        for code, label in (("ADMIN_SCOPE_CHANGED", "Program/Major Updated"),
                            ("EMAIL_VERIFICATION_INITIATED", "Email Verification Initiated"),
                            ("EMAIL_VERIFICATION_CODE_SENT", "Email Verification Code Sent"),
                            ("login_success", "Logged In")):
            with self.subTest(code=code):
                recorded_text = f"{code.replace('_', ' ').title()} by 2023304615"
                event = self.event(activity_type=code, activity=recorded_text)
                response = self.client.get(self.url)
                row = next(row for row in response.context["users"] if row["ref"] == f"mobile:{self.student.pk}")
                self.assertEqual(row["last_activity"], label)
                student_drawer = next(row for row in response.context["users_json"] if row["ref"] == f"mobile:{self.student.pk}")
                self.assertEqual(student_drawer["lastActivity"], label)
                self.assertEqual(response.context["recent_activities"][0]["detail"]["action"], label)
                self.assertEqual(AccountActivity.objects.get(pk=event.pk).activity, recorded_text)

    def test_legacy_guest_role_is_user_in_activity_details(self):
        self.event(self.guest)
        response = self.client.get(self.url)
        self.assertEqual(response.context["recent_activities"][0]["detail"]["performed_by"]["role"], "User")
        self.assertNotContains(response, "Standard User")

    def test_one_period_controls_login_counts_failures_peak_and_log(self):
        self.event()
        self.event(activity_type="login_failed", activity="Failed login attempt", result="failed")
        older = self.event(activity_type="login_failed", activity="Old failed attempt", result="failed")
        AccountActivity.objects.filter(pk=older.pk).update(created_at=self.now - timedelta(days=20))
        response = self.client.get(self.url, {"period": "today"})
        self.assertEqual(response.context["failed_login_attempts"], 1)
        data = response.context["monitor_chart_data"]
        for grouping in ("daily", "weekly", "monthly"):
            self.assertEqual(sum(data[grouping]["success"]), 1)
        self.assertEqual(sum(data["peakHours"]["values"]), 1)
        self.assertEqual(response.context["activity_page_obj"].paginator.count, 2)
        # Drawer history is intentionally all-time; only the global log is period-bound.
        self.assertNotIn(str(older.pk), {row["id"] for row in response.context["recent_activities"]})

    def test_actor_and_target_are_resolved_separately_and_action_is_concise(self):
        role = Role.objects.create(role_name="Monitoring Test Role")
        event = self.event(self.admin, module="Roles & Permissions", activity_type="ROLE_DEACTIVATED",
                           activity="Role Deactivated: Monitoring Test Role by monitor-owner",
                           metadata={"actor_admin_id": self.admin.pk, "role_id": str(role.pk), "role_name": role.role_name})
        row = event_rows([event])[0]
        self.assertEqual(row["actor"], "monitor-owner")
        self.assertEqual(row["target"], role.role_name)
        self.assertEqual(row["action"], "Role Deactivated")
        event.activity_type = "ADMIN_ASSIGNED_TO_ROLE"
        event.metadata["target_admin_id"] = self.admin.pk
        self.assertEqual(event_rows([event])[0]["target"], "monitor-owner")
        event.activity_type = "ROLE_DEACTIVATED"
        product = Product.objects.create(name="Real Target Product", seller=self.admin, price=50)
        event.metadata = {"actor_admin_id": self.admin.pk, "product_id": product.pk}
        self.assertEqual(event_rows([event])[0]["target"], product.name)
        event.metadata = {"role_id": "not-a-uuid"}
        self.assertEqual(event_rows([event])[0]["target"], "\u2014")
        self.assertEqual(event_rows([event])[0]["actor"], "Unknown")

    def test_historical_metadata_and_session_secrets_never_reach_page(self):
        self.event(metadata={"password": "secret-password-example", "verification_code": "secret-code-example",
                             "token": "secret-token-example", "session_id": "secret-session-example",
                             "previous": {"status": "pending", "password": "nested-secret-example"}},
                   session_identifier="historic-raw-session-example")
        response = self.client.get(self.url)
        for secret in ("secret-password-example", "secret-code-example", "secret-token-example", "secret-session-example", "nested-secret-example", "historic-raw-session-example"):
            self.assertNotContains(response, secret)
        self.assertNotIn("metadata", response.context["recent_activities"][0])

    def test_logger_removes_credentials_and_reuses_one_audit_row(self):
        request = RequestFactory().post("/existing-action/")
        request.user = self.admin
        event = log_account_activity(request, source="mobile", account=self.student, module="User Management",
            activity_type="USER_UPDATED", activity="User Updated", result="success", session_identifier="private-session",
            metadata={"password": "private", "new": {"status": "active", "refresh_token": "private-token"}})
        self.assertEqual(event.session_identifier, "")
        self.assertNotIn("password", event.metadata)
        self.assertEqual(event.metadata["new"], {"status": "active"})
        self.assertEqual(event.metadata["actor_admin_id"], self.admin.pk)
        self.assertEqual(AccountActivity.objects.count(), 1)

    def test_log_pagination_filters_and_sql_bounded_drawer(self):
        for number in range(45):
            self.event(activity_type="USER_UPDATED", activity=f"Test event {number}")
        response = self.client.get(self.url, {"q": "monitor-student", "activity_page": 2})
        self.assertEqual(len(response.context["recent_activities"]), 20)
        self.assertEqual(response.context["activity_page_obj"].number, 2)
        student = next(row for row in response.context["users_json"] if row["ref"] == f"mobile:{self.student.pk}")
        self.assertEqual(len(student["events"]), 20)
        self.assertContains(response, "Clear Filters")
        self.assertEqual(self.client.get(self.url, {"type": "guest"}).context["activity_page_obj"].paginator.count, 0)
        self.assertEqual(self.client.get(self.url).context["paginator"].count, 3)

    def test_database_failure_shows_retry_without_fake_counts(self):
        with patch("accounts.views.build_account_rows", side_effect=DatabaseError("Test failure")):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Unable to load user monitoring.", status_code=503)
        self.assertContains(response, "Retry", status_code=503)
        self.assertNotContains(response, "Enabled user accounts", status_code=503)

    def test_export_browser_fixture_from_test_database_only(self):
        self.token("never-export-this-session-key")
        self.event()
        self.event(activity_type="login_failed", activity="Failed login attempt", result="failed")
        response = self.client.get(self.url)
        folder = os.environ.get("MONITOR_REVIEW_DIR")
        if folder:
            target = Path(folder)
            target.mkdir(parents=True, exist_ok=True)
            (target / "monitoring.html").write_bytes(response.content)
            with patch("accounts.views.build_account_rows", side_effect=DatabaseError("Test failure")):
                (target / "error.html").write_bytes(self.client.get(self.url).content)
