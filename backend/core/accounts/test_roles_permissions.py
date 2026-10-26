"""Isolated regression tests for the existing RBAC and staged Roles UI."""
import importlib
import json
import os
import re
from pathlib import Path

from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import AccountActivity, Department, ProgramMajor, Role, User
from .role_management import eligible_admin_queryset, serialize_role
from .role_permissions import (
    ADMIN_UI_PERMISSION_CODENAMES, BUILTIN_ROLE_PERMISSIONS, set_role_permissions,
    sync_user_admin_permissions, PERMISSION_DEPENDENCIES,
)
from api.models import Booking, CampusHubUser, Facility, FacilityBookingRequest, FacilityPayment, Product, Room


class RolesWorkflowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Legacy unmanaged tables are not created by ordinary Django migrations.
        # Create empty model-accurate tables only in the isolated test database.
        for model in (CampusHubUser, Facility, Room, Booking, FacilityBookingRequest, FacilityPayment):
            if model._meta.db_table not in connection.introspection.table_names():
                with connection.schema_editor() as editor:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.super = User.objects.create_superuser(username="roles-review-super", role="Super Admin")
        self.client.force_login(self.super)
        self.roles = {name: Role.objects.get_or_create(role_name=name)[0] for name in BUILTIN_ROLE_PERMISSIONS}
        for name, role in self.roles.items():
            set_role_permissions(role, list(BUILTIN_ROLE_PERMISSIONS[name]))
        self.role = Role.objects.create(role_name="Inventory Reader", description="Read-only stock monitoring.")
        set_role_permissions(self.role, ["can_view_inventory"])
        self.candidate = User.objects.create_user(username="existing-admin", is_staff=True, role="User")
        self.normal = User.objects.create_user(username="ordinary-buyer", role="User")

    def post(self, route, **data):
        return self.client.post(reverse(route), data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def assign(self, role=None, **extra):
        data = {"operation": "assign", "role_id": (role or self.role).pk,
                "assigned_users": [self.candidate.pk], "confirm_role_changes": "1"}
        data.update(extra)
        return self.post("admin_roles_save", **data)

    def test_real_kpis_exclude_normal_accounts_and_base_assignment(self):
        page = self.client.get(reverse("admin_roles_page"))
        self.assertEqual(page.context["assigned_admins"], 1)
        self.assertEqual(page.context["unassigned_admins"], 1)
        self.assertEqual(page.context["total_permission_count"], Permission.objects.filter(
            content_type__app_label="accounts", content_type__model="role", codename__in=ADMIN_UI_PERMISSION_CODENAMES).count())
        self.assertEqual(page.context["total_roles"], Role.objects.count() - 1)
        self.assertNotIn("User", {r["role_name"] for r in page.context["roles"]})
        self.assertNotContains(page, "Standard User")
        self.assertNotContains(page, "Base User Access")
        self.assertTrue(Role.objects.filter(pk=self.roles["User"].pk).exists())
        self.assertNotIn(self.normal.pk, {u["id"] for u in page.context["assignable_admins"]})

    def test_protected_direct_posts_leave_grants_and_identities_intact(self):
        for name in ("Super Admin", "User"):
            role = self.roles[name]
            previous = set(role.granted_permissions.values_list("pk", flat=True))
            self.assertEqual(self.post("admin_role_permissions_save", role_id=role.pk, permissions=[]).status_code, 400)
            self.assertEqual(self.post("admin_roles_save", role_id=role.pk, role_name="Renamed Role").status_code, 400)
            self.assertEqual(self.post("admin_roles_status", role_id=role.pk, action="deactivate").status_code, 400)
            self.assertEqual(self.post("admin_roles_delete", role_id=role.pk).status_code, 400)
            self.assertEqual(set(role.granted_permissions.values_list("pk", flat=True)), previous)
        for name in ("Marketplace Admin", "Facilities Admin"):
            self.assertEqual(self.post("admin_roles_save", role_id=self.roles[name].pk, role_name="Changed Identity").status_code, 400)

    def test_reserved_standard_user_alias_cannot_create_a_second_base_role(self):
        self.assertEqual(self.post("admin_roles_save", role_name="standard user").status_code, 400)

    def test_information_changes_preserve_grants_and_assignments(self):
        self.assign()
        before = set(self.role.granted_permissions.values_list("pk", flat=True))
        result = self.post("admin_roles_save", role_id=self.role.pk, role_name="Stock Reader", description="Updated role information", permissions=["can_system_backup"])
        self.assertEqual(result.status_code, 200)
        self.role.refresh_from_db(); self.candidate.refresh_from_db()
        self.assertEqual(set(self.role.granted_permissions.values_list("pk", flat=True)), before)
        self.assertEqual(self.candidate.role, "Stock Reader")

    def test_creation_rejects_early_assignment_then_opens_configuration(self):
        result = self.post("admin_roles_save", role_name="New Desk", assigned_users=[self.candidate.pk])
        self.assertEqual(result.status_code, 400)
        self.assertFalse(Role.objects.filter(role_name="New Desk").exists())
        result = self.post("admin_roles_save", role_name="New Desk", permissions=["can_manage_orders"])
        self.assertEqual(result.status_code, 200)
        role = Role.objects.get(role_name="New Desk")
        self.assertFalse(role.granted_permissions.exists())
        self.assertEqual(self.assign(role).status_code, 400)
        configured = self.post("admin_role_permissions_save", role_id=role.pk, permissions=["can_view_orders"])
        self.assertEqual(configured.status_code, 200)
        self.assertEqual(self.assign(role).status_code, 200)
        page = self.client.get(reverse("admin_roles_page"), {"configure": role.pk})
        self.assertEqual(page.context["configure_role"]["id"], str(role.pk))

    def test_assignment_requires_confirmation_and_rejects_normal_accounts(self):
        self.assertEqual(self.assign(confirm_role_changes="").status_code, 400)
        self.assertEqual(self.assign(assigned_users=[self.normal.pk]).status_code, 400)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.role, "User")
        self.assertEqual(self.assign().status_code, 200)

    def test_final_active_super_admin_cannot_be_demoted(self):
        result = self.assign(assigned_users=[self.super.pk])
        self.assertEqual(result.status_code, 400)
        self.assertIn("final active Super Admin", result.json()["message"])
        self.super.refresh_from_db()
        self.assertTrue(self.super.is_superuser)

    def test_marketplace_assignment_reuses_program_major_validation(self):
        market = self.roles["Marketplace Admin"]
        self.assertEqual(self.assign(market).status_code, 400)
        btled = Department.objects.get(code="BTLED")
        self.candidate.department = btled; self.candidate.save()
        self.assertEqual(self.assign(market).status_code, 400)
        self.candidate.major = ProgramMajor.objects.get(program=btled, code="HE"); self.candidate.save()
        self.assertEqual(self.assign(market).status_code, 200)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.major.code, "HE")

    def test_global_facility_assignment_clears_inapplicable_academic_scope(self):
        self.candidate.department = Department.objects.get(code="BSIT"); self.candidate.save()
        self.assertEqual(self.assign(self.roles["Facilities Admin"]).status_code, 200)
        self.candidate.refresh_from_db()
        self.assertIsNone(self.candidate.department)
        self.assertIsNone(self.candidate.major)

    def test_inactive_role_rejects_assignment_without_losing_history(self):
        self.assertEqual(self.assign().status_code, 200)
        self.assertEqual(self.post("admin_roles_status", role_id=self.role.pk, action="deactivate").status_code, 200)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.role, self.role.role_name)
        self.assertFalse(self.candidate.has_perm("accounts.can_view_inventory"))
        self.assertEqual(self.assign().status_code, 400)
        self.assertEqual(self.post("admin_roles_status", role_id=self.role.pk, action="activate").status_code, 200)
        self.candidate.refresh_from_db()
        self.candidate = User.objects.get(pk=self.candidate.pk) # Fresh request objects have fresh permission caches.
        self.assertTrue(self.candidate.has_perm("accounts.can_view_inventory"))

    def test_ordinary_capabilities_survive_permission_edits(self):
        market = self.roles["Marketplace Admin"]
        result = self.post("admin_role_permissions_save", role_id=market.pk, permissions=["can_view_orders", "can_manage_facilities", "can_restore_system_backup"])
        self.assertEqual(result.status_code, 200)
        grants = set(market.granted_permissions.values_list("codename", flat=True))
        self.assertIn("can_buy_products", grants)
        self.assertIn("can_browse_products", grants)
        self.assertIn("can_view_orders", grants)
        self.assertNotIn("can_manage_facilities", grants)
        self.assertNotIn("can_restore_system_backup", grants)

    def test_mutations_store_actor_target_previous_new_timestamp(self):
        self.assign()
        event = AccountActivity.objects.get(activity_type="ADMIN_ROLE_CHANGED")
        self.assertEqual(event.account_id, self.candidate.pk)
        self.assertEqual(event.metadata["actor_admin_id"], self.super.pk)
        self.assertEqual(event.metadata["target_admin_id"], self.candidate.pk)
        self.assertEqual(event.metadata["previous"], "User")
        self.assertEqual(event.metadata["new"], self.role.role_name)
        self.assertIsNotNone(event.created_at)
        self.assertNotIn("password", str(event.metadata))
        self.assertEqual(self.post("admin_roles_delete", role_id=self.role.pk).status_code, 400)
        self.post("admin_roles_save", role_name="Historical Desk")
        role = Role.objects.get(role_name="Historical Desk")
        self.assertEqual(self.post("admin_roles_delete", role_id=role.pk).status_code, 400)

    def test_unknown_input_and_unprivileged_role_posts_fail_safely(self):
        self.assertEqual(self.post("admin_roles_status", role_id="invalid", action="activate").status_code, 400)
        self.client.force_login(self.normal)
        for route in ("admin_roles_save", "admin_role_permissions_save", "admin_roles_status", "admin_roles_delete"):
            self.assertEqual(self.post(route, role_id=self.role.pk, role_name="Unauthorized").status_code, 403)

    def test_inventory_read_permission_does_not_grant_writes_or_movements(self):
        self.assign(); self.candidate.refresh_from_db(); self.client.force_login(self.candidate)
        self.assertEqual(self.client.get(reverse("admin_products_page"), {"view": "inventory"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("seller_products_monitor")).status_code, 200)
        self.assertNotEqual(self.client.get(reverse("admin_products_page")).status_code, 200)
        self.assertEqual(self.client.post(reverse("admin_save_product"), {}).status_code, 403)
        self.assertFalse(self.candidate.has_perm("accounts.can_view_stock_movements"))

    def test_read_permissions_use_real_scoped_products_without_stock_history(self):
        program = Department.objects.get(code="BSIT")
        self.candidate.department = program; self.candidate.save()
        local = Product.objects.create(seller=self.normal, name="Scoped Product", department=program, price=10, stock=4)
        foreign = Product.objects.create(seller=self.normal, name="Other Program", department=Department.objects.get(code="BFPT"), price=10, stock=9)
        self.assign(); self.client.force_login(self.candidate)
        result = self.client.get(reverse("seller_products_monitor"), {"product_id": local.pk})
        self.assertEqual(result.status_code, 200)
        product = result.json()["products"][0]
        self.assertIn("inventory", product)
        self.assertFalse(product["can_view_stock_movements"])
        self.assertNotIn("stock_movements", product)
        self.assertEqual(self.client.get(reverse("seller_products_monitor"), {"product_id": foreign.pk}).json()["products"], [])

    def test_view_orders_and_facilities_do_not_enable_operational_writes(self):
        set_role_permissions(self.role, ["can_view_orders", "can_view_facilities", "can_view_bookings", "can_view_sellers"])
        self.assign(); self.client.force_login(self.candidate)
        for route in ("admin_orders_page", "admin_facility_page", "admin_bookings_page", "admin_sellers_page"):
            self.assertEqual(self.client.get(reverse(route)).status_code, 200, route)
        self.assertEqual(self.client.post(reverse("admin_order_update", args=[999999]), {}).status_code, 403)
        self.assertNotEqual(self.client.post(reverse("facilities_update", args=["missing"]), {}).status_code, 200)

    def test_legacy_timestamp_is_honest_and_read_grant_migration_is_additive(self):
        Role.objects.filter(pk=self.role.pk).update(updated_at=None)
        self.role.refresh_from_db()
        self.assertEqual(serialize_role(self.role)["updated_date"], "—")
        set_role_permissions(self.role, ["can_manage_orders", "can_buy_products"])
        old_grants = set(self.role.granted_permissions.values_list("pk", flat=True))
        migration = importlib.import_module("accounts.migrations.0026_role_management_audit")
        with connection.schema_editor() as editor:
            migration.preserve_read_access(apps, editor)
        self.assertTrue(old_grants.issubset(set(self.role.granted_permissions.values_list("pk", flat=True))))
        self.assertTrue(self.role.granted_permissions.filter(codename="can_view_orders").exists())

    def test_page_batches_role_permissions_and_admins_and_exports_browser_fixture(self):
        self.assign()
        with CaptureQueriesContext(connection) as before:
            page = self.client.get(reverse("admin_roles_page"))
        for index in range(12):
            role = Role.objects.create(role_name=f"Reader {index}")
            set_role_permissions(role, ["can_view_orders"])
        with CaptureQueriesContext(connection) as after:
            page = self.client.get(reverse("admin_roles_page"))
        self.assertLessEqual(len(after), len(before) + 2)
        self.assertEqual([g["name"] for g in page.context["permission_groups"]], ["Marketplace", "Facilities", "User Management", "Reports", "System"])
        self.assertNotContains(page, 'value="can_buy_products"')
        if os.environ.get("ROLES_REVIEW_DIR"):
            folder = Path(os.environ["ROLES_REVIEW_DIR"]); folder.mkdir(parents=True, exist_ok=True)
            (folder / "roles.html").write_bytes(page.content)
            filtered = self.client.get(reverse("admin_roles_page"), {"q": "No such role"})
            (folder / "empty.html").write_bytes(filtered.content)

    def test_single_action_menu_matches_each_role_and_configuration_state(self):
        inactive = Role.objects.create(role_name="Inactive Reader", is_active=False)
        set_role_permissions(inactive, ["can_view_inventory"])
        unconfigured = Role.objects.create(role_name="Unconfigured Reader")
        page = self.client.get(reverse("admin_roles_page")); html = page.content.decode()
        self.assertEqual(re.findall(r"<th>(.*?)</th>", html), ["Role", "Role Type", "Assigned Admins", "Access Level", "Status", "Last Updated", "Actions"])
        common = ["View Permissions", "Edit Permissions", "View Assigned Administrators", "Assign Administrators", "View Permission History"]
        for role in [*[r for name, r in self.roles.items() if name != "User"], self.role, inactive, unconfigured]:
            with self.subTest(role=role.role_name):
                row_match = re.search(r'<tr data-role-row="' + str(role.pk) + r'">(.*?)</tr>', html, re.S)
                assert row_match is not None
                row = row_match.group(1)
                self.assertEqual(row.count('class="role-icon-action role-more-toggle"'), 1)
                self.assertNotIn('role-icon-edit', row)
                self.assertIn('aria-label="More actions"', row); self.assertIn('title="More Actions"', row)
                # Only the menu items are secondary buttons; no other inline actions.
                outside_menu = re.sub(r'<ul.*?</ul>', '', row, flags=re.S)
                self.assertEqual(outside_menu.count('<button'), 1)
                actions = [label for hidden, label in re.findall(r'<li( hidden)?><button[^>]*class="dropdown-item[^>]*>([^<]+)</button></li>', row) if not hidden]
                if role.role_name == "Super Admin":
                    self.assertEqual(actions, ["View Permissions"])
                elif role.role_name in ("Marketplace Admin", "Facilities Admin"):
                    self.assertEqual(actions, common)
                else:
                    expected = common if role == self.role else [a for a in common if a != "Assign Administrators"]
                    self.assertEqual(actions, expected + ["Edit Role Information", "Deactivate Role" if role.is_active else "Reactivate Role"])
                self.assertNotIn('Delete Role', row)

    def test_assigned_administrators_include_truthful_account_status(self):
        self.assign(); self.candidate.refresh_from_db()
        self.candidate.is_suspended = True; self.candidate.save(update_fields=["is_suspended"])
        rows = serialize_role(self.role)["role_users"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["account_status"], "Suspended")
        self.assertNotIn(self.normal.pk, {row["id"] for row in rows})

    def test_history_reads_existing_role_audit_only_with_pagination_and_no_writes(self):
        events = [AccountActivity(account_source="admin", account_id=self.super.pk,
            account_ref=f"admin:{self.super.pk}", username=self.super.username,
            activity_type="PERMISSIONS_CHANGED", activity=f"Recorded change {i}", module="Roles & Permissions",
            metadata={"role_id": str(self.role.pk), "password": "never-return-test-marker"}) for i in range(25)]
        AccountActivity.objects.bulk_create(events)
        AccountActivity.objects.create(account_source="admin", activity_type="ROLE_UPDATED", activity="Other role", module="Roles & Permissions", metadata={"role_id": str(self.roles["Marketplace Admin"].pk)})
        AccountActivity.objects.create(account_source="admin", activity_type="ACCOUNT_RECOVERY_INITIATED", activity="Unrelated module", module="Authentication", metadata={"role_id": str(self.role.pk)})
        before = AccountActivity.objects.count(); grants = set(self.role.granted_permissions.values_list('pk', flat=True))
        page = self.client.get(reverse("admin_roles_page"), {"history_role": self.role.pk})
        self.assertEqual(page.status_code, 200); self.assertEqual(page.json()["total"], 25)
        self.assertEqual(len(page.json()["events"]), 20); self.assertTrue(page.json()["has_next"])
        self.assertEqual(page["Cache-Control"], "no-store")
        self.assertNotContains(page, 'never-return-test-marker'); self.assertNotContains(page, 'Other role')
        next_page = self.client.get(reverse("admin_roles_page"), {"history_role": self.role.pk, "history_page": 2}).json()
        self.assertEqual(len(next_page["events"]), 5); self.assertFalse(next_page["has_next"])
        self.assertGreater(page.json()["events"][0]["id"], next_page["events"][0]["id"])
        self.assertEqual(AccountActivity.objects.count(), before)
        self.assertEqual(set(self.role.granted_permissions.values_list('pk', flat=True)), grants)
        self.post("admin_roles_save", role_id=self.role.pk, role_name="Renamed Reader")
        history = self.client.get(reverse("admin_roles_page"), {"history_role": self.role.pk}).json()
        self.assertEqual(history["total"], 26)  # Stable role ID preserves history across renames.

    def test_history_empty_invalid_method_and_authorization(self):
        url = reverse("admin_roles_page")
        response = self.client.get(url, {"history_role": self.role.pk})
        self.assertEqual(response.json()["events"], []); self.assertEqual(response.json()["total"], 0)
        self.assertEqual(self.client.get(url, {"history_role": "invalid"}).status_code, 404)
        self.assertEqual(self.client.post(url + "?history_role=" + str(self.role.pk)).status_code, 405)
        for role_name in ("Marketplace Admin", "Facilities Admin", self.role.role_name):
            actor = User.objects.create_user(username=role_name.replace(' ', '-'), role=role_name)
            self.client.force_login(actor)
            self.assertEqual(self.client.get(url, {"history_role": self.role.pk}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url, {"history_role": self.role.pk}).status_code, 302)

    def test_export_action_browser_fixtures(self):
        if not os.environ.get("ROLES_REVIEW_DIR"):
            return
        self.assign()
        inactive = Role.objects.create(role_name="Inactive Reader", is_active=False)
        set_role_permissions(inactive, ["can_view_inventory"])
        unconfigured = Role.objects.create(role_name="Unconfigured Reader")
        folder = Path(os.environ["ROLES_REVIEW_DIR"]); folder.mkdir(parents=True, exist_ok=True)
        (folder / "actions.html").write_bytes(self.client.get(reverse("admin_roles_page")).content)
        (folder / "history.json").write_text(json.dumps(self.client.get(reverse("admin_roles_page"), {"history_role": self.role.pk}).json()), encoding="utf-8")

    def test_hidden_base_roles_preserve_grants_accounts_and_normal_mobile_login(self):
        base = self.roles["User"]
        before = set(base.granted_permissions.values_list("pk", flat=True))
        alias = Role.objects.create(role_name="Standard User")
        for kind in ("student", "guest"):
            user = CampusHubUser.objects.create(username=f"base-{kind}", email=f"base-{kind}@example.com",
                first_name="Ordinary", last_name="User", user_type=kind, role="User",
                password_hash=make_password("Test-only-pass-82"), profile_completed=True)
            result = self.client.post(reverse("mobile_login"),
                data=json.dumps({"student_id_or_email": user.username, "password": "Test-only-pass-82"}),
                content_type="application/json")
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["user"]["role"], "User")
            user.refresh_from_db(); self.assertEqual(user.role, "User")
        for params in ({}, {"type": "system"}, {"q": "Standard User"}, {"configure": base.pk}):
            page = self.client.get(reverse("admin_roles_page"), params)
            self.assertEqual(page.context["total_roles"], Role.objects.count() - 2)
            self.assertNotIn("User", {r["role_name"] for r in page.context["roles"]})
            self.assertNotContains(page, 'class="role-table-name">Standard User')
            self.assertIsNone(page.context["configure_role"])
        self.assertEqual(self.client.get(reverse("admin_roles_page"), {"history_role": base.pk}).status_code, 404)
        self.assertEqual(self.client.get(reverse("admin_roles_page"), {"history_role": alias.pk}).status_code, 404)
        self.assertEqual(self.post("admin_role_permissions_save", role_id=alias.pk, permissions=[]).status_code, 400)
        self.assertTrue(Role.objects.filter(pk=alias.pk).exists())
        self.assertEqual(set(base.granted_permissions.values_list("pk", flat=True)), before)
        self.normal.set_password("Normal-only-pass-82"); self.normal.save(update_fields=["password"])
        self.assertTrue(self.client.login(username=self.normal.username, password="Normal-only-pass-82"))

    def test_access_labels_and_protection_are_honest_in_existing_drawer(self):
        page = self.client.get(reverse("admin_roles_page"))
        labels = {r["role_name"]: r["permission_summary"] for r in page.context["roles"]}
        expected = {"Super Admin": "Full Access", "Marketplace Admin": "Marketplace Access", "Facilities Admin": "Facilities Access"}
        for name, label in expected.items():
            self.assertEqual(labels[name], label)
        self.assertTrue(all(label == "Custom Access" for name, label in labels.items() if name not in expected))
        self.assertContains(page, "Protected System Role", count=1)
        self.assertEqual(page.context["permission_dependencies"], PERMISSION_DEPENDENCIES)

    def test_dependencies_are_enforced_for_direct_posts_without_adding_write_authority(self):
        self.assign()
        for action, reads in PERMISSION_DEPENDENCIES.items():
            with self.subTest(action=action):
                result = self.post("admin_role_permissions_save", role_id=self.role.pk, permissions=[action])
                self.assertEqual(result.status_code, 200)
                self.assertEqual(set(result.json()["role"]["assigned_permissions"]), {action, *reads})
                self.assertEqual(set(self.role.granted_permissions.values_list("codename", flat=True)), {action, *reads})
                self.candidate.refresh_from_db()
                self.assertTrue(User.objects.get(pk=self.candidate.pk).has_perm(f"accounts.{reads[0]}"))
        # View-only selection must never grant its corresponding Manage action.
        result = self.post("admin_role_permissions_save", role_id=self.role.pk, permissions=["can_view_orders"])
        self.assertEqual(result.json()["role"]["assigned_permissions"], ["can_view_orders"])
        market = self.roles["Marketplace Admin"]
        result = self.post("admin_role_permissions_save", role_id=market.pk,
            permissions=["can_manage_facilities", "can_manage_products"])
        self.assertEqual(set(result.json()["role"]["assigned_permissions"]), {"can_manage_products", "can_view_products"})
        event = AccountActivity.objects.filter(activity_type="PERMISSIONS_CHANGED", metadata__role_id=str(market.pk)).latest("pk")
        self.assertIn("can_view_products", event.metadata["new"])
        self.assertNotIn("can_view_facilities", event.metadata["new"])

    def test_reassignment_audits_removal_under_original_role_and_keeps_records(self):
        self.assign()
        other = Role.objects.create(role_name="Order Reader")
        set_role_permissions(other, ["can_view_orders"])
        before = self.role.updated_at
        result = self.assign(other)
        self.assertEqual(result.status_code, 200)
        event = AccountActivity.objects.get(activity_type="ADMIN_REMOVED_FROM_ROLE")
        self.assertEqual(event.metadata["role_id"], str(self.role.pk))
        self.assertEqual(event.metadata["new"], other.role_name)
        self.assertEqual(event.metadata["target_admin_id"], self.candidate.pk)
        self.assertEqual(self.client.get(reverse("admin_roles_page"), {"history_role": self.role.pk}).json()["total"], 3)
        self.role.refresh_from_db(); self.assertGreater(self.role.updated_at, before)
        self.assertTrue(Role.objects.filter(pk=self.role.pk).exists())
        result = self.post("admin_roles_save", role_id=other.pk, role_name=other.role_name,
            role_status_present="1", is_active="")
        self.assertEqual(result.status_code, 200)
        self.assertTrue(AccountActivity.objects.filter(activity_type="ROLE_DEACTIVATED", metadata__role_id=str(other.pk)).exists())
