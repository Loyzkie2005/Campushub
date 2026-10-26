"""Activity web/DRF privacy, identity and scope tests; isolated test records only."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import jwt
from django.conf import settings
from django.contrib.auth.models import Permission
from django.db import DatabaseError, connection
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.activity_service import format_activities, parse_connection
from accounts.admin_tab_auth import create_admin_tab_token
from accounts.models import AccountActivity, AdminTabToken, Department, ProgramMajor, Role, User
from accounts.monitoring import event_rows
from accounts.role_permissions import BUILTIN_ROLE_PERMISSIONS, set_role_permissions, sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, MarketplaceOrder, Product, SellerRequest


@override_settings(TIME_ZONE="Asia/Manila")
class ActivityAPITests(TestCase):
    @classmethod
    def setUpClass(cls):
        # These legacy models are unmanaged; create missing tables in the TEST
        # database only, just as the project's existing tests do.
        existing = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Booking):
                if model._meta.db_table not in existing:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.api = APIClient()
        self.owner = User.objects.create_superuser(username="audit-owner", role="Super Admin", first_name="Audit", last_name="Owner")
        self.student = CampusHubUser.objects.create(username="audit-student", email="audit-student@example.com", first_name="Student", last_name="Example", role="User", user_type="student", password_hash="unused")
        self.event = AccountActivity.objects.create(account_source="mobile", account_id=self.student.pk,
            account_ref=f"mobile:{self.student.pk}", username=self.student.username,
            full_name="Student Example", role="User", account_type="student",
            activity_type="ACCOUNT_RECOVERY_INITIATED", activity="Account Recovery Initiated",
            module="User Management", result="success", ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/155.0.0.0 Safari/537.36",
            metadata={"actor_admin_id": self.owner.pk, "actor_username": self.owner.username})
        self.url = reverse("activity_log_detail", args=[self.event.pk])
        self.list_url = reverse("activity_log_list")
        self.api.force_login(self.owner)

    def detail(self):
        response = self.api.get(self.url)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["data"]

    def test_recovery_actor_target_and_same_web_service(self):
        data = self.detail()
        self.assertEqual(data["performed_by"], {"name": "Audit Owner", "username": "audit-owner", "role": "Super Admin"})
        self.assertEqual(data["affected_record"], {"type": "user", "label": "Affected User", "name": "Student Example"})
        self.assertEqual(data["action"], "Account Recovery Initiated")
        self.assertEqual(data, event_rows([self.event])[0]["detail"])
        self.client.force_login(self.owner)
        page = self.client.get(reverse("admin_user_monitoring_page"))
        self.assertEqual(page.context["recent_activities"][0]["detail"], data)

    def test_role_and_admin_assignment_targets(self):
        role = Role.objects.create(role_name="Audit Example Role")
        self.event.activity_type = "ROLE_DEACTIVATED"
        self.event.module = "Roles & Permissions"
        self.event.metadata["role_id"] = str(role.pk)
        self.event.save()
        self.assertEqual(self.detail()["affected_record"]["label"], "Affected Role")
        self.assertEqual(self.detail()["action"], "Role Deactivated")
        self.event.activity_type = "ADMIN_ROLE_CHANGED"
        self.event.metadata["target_admin_id"] = self.owner.pk
        self.event.save()
        self.assertEqual(self.detail()["affected_record"]["label"], "Affected User")

    def test_login_has_null_target_even_with_stale_target_metadata(self):
        self.event.activity_type = "login_success"
        self.event.module = "Authentication"
        self.event.metadata = {"role_id": "invalid", "target_admin_id": self.owner.pk}
        self.event.save()
        data = self.detail()
        self.assertIsNone(data["affected_record"])
        self.assertEqual(data["action"], "Logged In")
        self.assertEqual(data["performed_by"]["name"], "Student Example")

    def test_ids_secrets_metadata_and_raw_agent_never_serialized(self):
        self.event.metadata.update({"password": "secret-password-marker", "verification_code": "secret-code-marker",
            "new": {"access_token": "secret-token-marker", "user_id": 987},
            "previous": {"status": "active", "role_id": "private-role-marker"}})
        self.event.session_identifier = "private-session-marker"
        self.event.save()
        response = self.api.get(self.url)
        public = response.content.decode()
        self.assertNotIn("metadata", public)
        self.client.force_login(self.owner)
        web = self.client.get(reverse("admin_user_monitoring_page")).content.decode()
        for value in ("actor_admin_id", "target_admin_id", "private-role-marker", "secret-password-marker",
                      "secret-code-marker", "secret-token-marker", "private-session-marker", self.event.user_agent):
            self.assertNotIn(value, public)
            self.assertNotIn(value, web)
        self.assertEqual(response.json()["data"]["connection"], {
            "ip_address": "127.0.0.1", "device": "Windows Desktop", "browser": "Google Chrome"})

    def test_unknown_actor_not_invented_system_requires_evidence(self):
        self.event.metadata = {}
        self.event.save()
        self.assertEqual(self.detail()["performed_by"], {"name": "Unknown", "username": None, "role": None})
        self.event.metadata = {"system_generated": True}
        self.event.save()
        self.assertEqual(self.detail()["performed_by"], {"name": "CampusHub System", "username": None, "role": "System"})

    def test_deleted_actor_snapshot_has_no_invented_role(self):
        self.event.metadata = {"actor_admin_id": 99999999, "actor_username": "recorded-admin"}
        self.event.save()
        self.assertEqual(self.detail()["performed_by"]["username"], "recorded-admin")
        self.assertIsNone(self.detail()["performed_by"]["role"])

    def test_unknown_connection_and_missing_ip_use_honest_values(self):
        self.event.user_agent = "Unrecognized client"
        self.event.ip_address = None
        self.event.save()
        self.assertEqual(self.detail()["connection"], {"ip_address": None, "device": "Unknown", "browser": "Unknown"})

    def test_entity_targets_and_string_booking_references(self):
        product = Product.objects.create(name="Audit Product", seller=self.owner, price=50)
        facility = Facility.objects.create(id="FAC-AUDIT", facility_name="Audit Facility")
        booking = Booking.objects.create(id="BK-AUDIT-001", facility=facility, user=self.student)
        order = MarketplaceOrder.objects.create(buyer_user_id=self.student.pk)
        seller = SellerRequest.objects.create(user=self.owner, student_id="EXAMPLE", full_name="Audit Seller", product_type="Food")
        for key, value, label, name in (
            ("product_id", product.pk, "Affected Product", product.name),
            ("facility_id", facility.pk, "Affected Facility", facility.facility_name),
            ("booking_id", booking.pk, "Affected Booking", booking.pk),
            ("order_id", order.pk, "Affected Order", order.order_code),
            ("seller_request_id", seller.pk, "Affected Seller", seller.full_name),
        ):
            with self.subTest(key=key):
                self.event.metadata = {"actor_admin_id": self.owner.pk, key: value}
                self.event.save()
                self.assertEqual(self.detail()["affected_record"]["label"], label)
                self.assertEqual(self.detail()["affected_record"]["name"], name)

    def test_invalid_historical_ids_do_not_crash_or_leak(self):
        for key, value in (("role_id", "invalid-uuid"), ("product_id", "not-a-number"), ("booking_id", "x" * 100)):
            self.event.metadata = {key: value}
            self.event.save()
            self.assertIsNone(self.detail()["affected_record"])

    def test_malformed_name_metadata_is_not_stringified(self):
        self.event.metadata = {"actor_username": {"password": "nested-secret-marker"},
            "role_id": "invalid", "role_name": ["nested-secret-marker"]}
        self.event.save()
        data = self.detail()
        self.assertEqual(data["performed_by"]["name"], "Unknown")
        self.assertIsNone(data["affected_record"])
        self.assertNotIn("nested-secret-marker", json.dumps(data))
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse("admin_user_monitoring_page")), "nested-secret-marker")

    def test_anonymous_401_normal_user_and_facilities_403(self):
        self.api.logout()
        response = self.api.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])
        for role in ("User", "Facilities Admin", "Custom Administrator"):
            actor = User.objects.create_user(username=f"audit-{role}", role=role)
            actor.user_permissions.add(Permission.objects.get(codename="can_view_user_monitoring"))
            self.api.force_login(actor)
            self.assertEqual(self.api.get(self.url).status_code, 403)

    def test_authenticated_mobile_student_jwt_is_denied_403(self):
        self.api.logout()
        token = jwt.encode({"sub": f"mobile:{self.student.pk}", "exp": timezone.now() + timedelta(minutes=5),
            "iss": "campushub-django", "aud": "campushub-chat"}, settings.CHAT_JWT_SECRET, algorithm=settings.CHAT_JWT_ALGORITHM)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.api.get(self.url).status_code, 403)

    def test_existing_tab_token_and_invalid_token_fail_closed(self):
        key = create_admin_tab_token(self.owner)
        self.api.logout()
        self.api.credentials(HTTP_X_ADMIN_TAB_TOKEN=key)
        self.assertEqual(self.api.get(self.url).status_code, 200)
        self.api.force_login(self.owner)
        self.api.credentials(HTTP_X_ADMIN_TAB_TOKEN="invalid-tab-marker")
        self.assertEqual(self.api.get(self.url).status_code, 401)
        AdminTabToken.objects.filter(key=key).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.api.credentials(HTTP_X_ADMIN_TAB_TOKEN=key)
        self.assertEqual(self.api.get(self.url).status_code, 401)

    def test_marketplace_scope_detail_list_and_connection_privacy(self):
        program = Department.objects.get(code="BTLED")
        major = ProgramMajor.objects.get(program=program, code="HE")
        other_major = ProgramMajor.objects.get(program=program, code="IA")
        self.student.department, self.student.major = program, major
        self.student.save()
        role = Role.objects.get_or_create(role_name="Marketplace Admin")[0]
        set_role_permissions(role, list(BUILTIN_ROLE_PERMISSIONS[role.role_name]))
        actor = User.objects.create_user(username="audit-scope", role=role.role_name, department=program, major=major)
        sync_user_admin_permissions(actor)
        foreign = CampusHubUser.objects.create(username="audit-foreign", email="audit-foreign@example.com", role="User", user_type="student", department=program, major=other_major)
        outside = AccountActivity.objects.create(account_ref=f"mobile:{foreign.pk}", account_source="mobile",
            account_id=foreign.pk, activity_type="ACCOUNT_RECOVERY_INITIATED", activity="Out of scope",
            module="User Management", result="success")
        self.api.force_login(actor)
        self.assertIsNone(self.detail()["connection"])
        self.assertEqual(self.api.get(reverse("activity_log_detail", args=[outside.pk])).status_code, 404)
        rows = self.api.get(self.list_url).json()["data"]
        self.assertEqual([row["id"] for row in rows], [self.event.pk])
        folder = os.environ.get("ACTIVITY_REVIEW_DIR")
        if folder:
            self.client.force_login(actor)
            page = self.client.get(reverse("admin_user_monitoring_page"))
            (Path(folder) / "scoped-activity.html").write_bytes(page.content)
        self.event.metadata["major_id"] = other_major.pk
        self.event.save()
        self.assertEqual(self.api.get(self.url).status_code, 404)
        self.assertEqual(self.api.get(self.list_url).json()["pagination"]["count"], 0)

    def test_list_paginated_minimal_and_does_not_echo_tab_secret(self):
        for _ in range(24):
            AccountActivity.objects.create(account_source="admin", username="pagination-owner", activity_type="login_success",
                activity="Logged In", module="Authentication", result="success")
        key = create_admin_tab_token(self.owner)
        response = self.api.get(self.list_url, {"__at": key, "page": 2})
        payload = response.json()
        self.assertEqual(len(payload["data"]), 5)
        self.assertEqual(payload["pagination"]["count"], 25)
        self.assertNotIn(key, response.content.decode())
        self.assertSetEqual(set(payload["data"][0]), {"id", "date_time", "performed_by", "action", "module", "result"})
        self.assertEqual(self.api.get(self.list_url, {"page": 99}).status_code, 404)
        self.assertEqual(self.api.get(self.list_url, {"page_size": 1000}).json()["pagination"]["page_size"], 100)

    def test_filters_dates_timezone_and_invalid_dates(self):
        when = timezone.make_aware(datetime(2026, 10, 10, 23, 59))
        AccountActivity.objects.filter(pk=self.event.pk).update(created_at=when)
        response = self.api.get(self.list_url, {"date_from": "2026-10-10", "date_to": "2026-10-10", "actor": self.owner.username,
            "search": "audit-student", "account_type": "student", "module": "User Management", "result": "success"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pagination"]["count"], 1)
        self.assertTrue(response.json()["data"][0]["date_time"].endswith("+08:00"))
        self.assertEqual(self.api.get(self.list_url, {"date_from": "2026-10-11"}).json()["data"], [])
        for params in ({"date_from": "2026-02-31"}, {"date_to": "bad"}, {"date_from": "2026-10-11", "date_to": "2026-10-10"}, {"date_to": "9999-12-31"}):
            response = self.api.get(self.list_url, params)
            self.assertEqual(response.status_code, 400)
            self.assertFalse(response.json()["success"])

    def test_missing_record_database_failure_and_read_only_methods(self):
        self.assertEqual(self.api.get(reverse("activity_log_detail", args=[99999999])).status_code, 404)
        with patch("api.activity_api.support_activity", side_effect=DatabaseError("secret database details")):
            response = self.api.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret database details", response.content.decode())
        self.assertEqual(self.api.post(self.list_url, {}).status_code, 405)
        self.assertEqual(AccountActivity.objects.count(), 1)
        self.assertEqual(self.api.get(self.url)["Cache-Control"], "no-store")

    def test_batch_resolution_has_no_per_row_queries(self):
        events = [self.event] * 30
        with self.assertNumQueries(1):
            details = format_activities(events)
        self.assertEqual(len(details), 30)

    def test_browser_signatures_without_unjustified_windows_version(self):
        for agent, device, browser in (
            ("Windows NT 10.0 Chrome/155.0 Edg/155.0", "Windows Desktop", "Microsoft Edge"),
            ("Android Chrome/150.0", "Android Device", "Google Chrome"),
            ("iPhone Version/18.0 Safari/605", "iPhone", "Safari"),
            ("Linux Firefox/140.0", "Linux Device", "Mozilla Firefox"),
            ("Windows NT 10.0 Chrome/155.0 OPR/120.0", "Windows Desktop", "Opera"),
            ("", "Unknown", "Unknown"),
        ):
            self.assertEqual(parse_connection(agent), {"ip_address": None, "device": device, "browser": browser})

    def test_export_safe_browser_fixture(self):
        folder = os.environ.get("ACTIVITY_REVIEW_DIR")
        if folder:
            self.client.force_login(self.owner)
            page = self.client.get(reverse("admin_user_monitoring_page"))
            target = Path(folder)
            target.mkdir(parents=True, exist_ok=True)
            (target / "activity.html").write_bytes(page.content)
            (target / "response.json").write_text(json.dumps(self.detail(), indent=2), encoding="utf-8")
