"""Academic scope, preserved archive history, and shared inventory identities."""
import json
import os
from pathlib import Path

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from accounts.academic import academic_options, resolve_academic, scope_products
from accounts.models import Department, ProgramMajor, User
from accounts.role_permissions import sync_user_admin_permissions
from accounts.views import get_notification_context
from api.models import InventoryStockMovement, MarketplaceOrder, Product, SellerRequest
from api.views import serialize_product
from .services.inventory import build_inventory_table
from .services.analytics import build_marketplace_analytics
from .services.order_access import admin_order_queryset
from .services.product_access import admin_product_queryset
from modules.reports.reporting import build_report


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ProgramInventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.btled, _ = Department.objects.get_or_create(code="BTLED", defaults={"name": "BTLED", "is_program": True})
        cls.bsit, _ = Department.objects.get_or_create(code="BSIT", defaults={"name": "BSIT", "is_program": True})
        Department.objects.get_or_create(code="BFPT", defaults={"name": "BFPT", "is_program": True})
        cls.he, _ = ProgramMajor.objects.get_or_create(program=cls.btled, code="HE", defaults={"name": "Home Economics"})
        cls.ia, _ = ProgramMajor.objects.get_or_create(program=cls.btled, code="IA", defaults={"name": "Industrial Arts"})
        ProgramMajor.objects.get_or_create(program=cls.btled, code="ICT", defaults={"name": "Information and Communication Technology"})
        cls.admin = User.objects.create_user(username="he-admin", role="Marketplace Admin", is_staff=True, department=cls.btled, major=cls.he)
        cls.super_admin = User.objects.create_superuser(username="academic-super", password="CampusHub1!", role="Super Admin")
        cls.no_scope = User.objects.create_user(username="unassigned-admin", role="Marketplace Admin", is_staff=True)
        for user in (cls.admin, cls.no_scope):
            sync_user_admin_permissions(user)
        cls.seller = User.objects.create_user(username="he-owner", department=cls.btled, major=cls.he)
        cls.foreign = User.objects.create_user(username="ia-owner", department=cls.btled, major=cls.ia)

    def setUp(self):
        self.client.force_login(self.admin)
        self.local = Product.objects.create(seller=self.seller, name="HE Product", department=self.btled, major=self.he,
                                            price=10, stock=3, low_stock_threshold=3, approval_status="approved")
        self.other = Product.objects.create(seller=self.foreign, name="IA Private Product", department=self.btled, major=self.ia,
                                            price=10, stock=7, low_stock_threshold=2, approval_status="approved")

    def save_product(self, **changes):
        data = {"name": "New product", "seller_id": self.seller.pk, "price": "10", "stock": 10,
                "low_stock_threshold": 3, "category": "School Supplies", "program_id": self.btled.pk, "major_id": self.he.pk}
        data.update(changes)
        return self.client.post(reverse("admin_save_product"), json.dumps(data), content_type="application/json")

    def order(self, product, code):
        return MarketplaceOrder.objects.create(product=product, order_code=code, product_name=product.name,
            quantity=1, unit_price=10, total_price=10, status="completed", payment_status="paid")

    def test_master_options_exist_independently_of_products(self):
        programs, majors = academic_options()
        self.assertTrue({"BSIT", "BFPT", "BTLED"}.issubset(set(programs.values_list("code", flat=True))))
        self.assertEqual(set(majors.filter(program=self.btled).values_list("code", flat=True)), {"IA", "HE", "ICT"})
        self.assertFalse(programs.filter(code__in=["HE", "IA", "ICT", "BTLED-HE"]).exists())

    def test_major_requires_its_own_program(self):
        with self.assertRaisesMessage(ValueError, "belonging"):
            resolve_academic(self.bsit.pk, self.he.pk, required=True)
        with self.assertRaisesMessage(ValueError, "major"):
            resolve_academic(self.btled.pk, required=True)

    def test_admin_scope_is_enforced_for_products_orders_and_inherited_programs(self):
        inherited = Product.objects.create(seller=self.seller, name="Legacy HE", price=10, stock=5)
        local_order = self.order(self.local, "HE-ORDER")
        self.order(self.other, "IA-ORDER")
        self.assertEqual(set(admin_product_queryset(self.admin).values_list("pk", flat=True)), {self.local.pk, inherited.pk})
        self.assertEqual(list(admin_order_queryset(self.admin).values_list("pk", flat=True)), [local_order.pk])
        self.assertEqual(admin_product_queryset(self.super_admin).count(), 3)
        self.assertFalse(admin_product_queryset(self.no_scope).exists())
        self.assertFalse(admin_order_queryset(self.no_scope).exists())
        program_admin = User.objects.create_user(username="program-admin", department=self.btled)
        # An incomplete BTLED assignment must fail closed until a major is assigned.
        self.assertEqual(scope_products(Product.objects.all(), program_admin).count(), 0)

    def test_page_api_and_detail_do_not_expose_other_major(self):
        for query in ({}, {"view": "inventory"}):
            page = self.client.get(reverse("admin_products_page"), query)
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, "HE Product")
            self.assertNotContains(page, "IA Private Product")
        detail = self.client.get(reverse("seller_products_monitor"), {"product_id": self.other.pk})
        self.assertEqual(detail.json()["products"], [])
        sku = self.other.inventory_skus.get(variant_name="")
        self.assertEqual(self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_item": sku.pk}).status_code, 404)

    def test_create_saves_program_major_and_inherits_reliable_owner_assignment(self):
        response = self.save_product()
        self.assertEqual(response.status_code, 201, response.content)
        payload = response.json()["product"]
        saved = Product.objects.get(pk=payload["id"])
        self.assertEqual((saved.department_id, saved.major_id), (self.btled.pk, self.he.pk))
        self.assertEqual(payload["program_major"], "BTLED-HE")
        self.assertNotEqual(payload["sku"], payload["product_code"])

    def test_write_checks_owner_scope_and_mismatched_major(self):
        self.assertEqual(self.save_product(seller_id=self.foreign.pk, major_id=self.ia.pk).status_code, 403)
        self.assertEqual(self.save_product(id=self.other.pk).status_code, 404)
        self.assertEqual(self.save_product(program_id=self.bsit.pk).status_code, 400)
        self.assertEqual(self.save_product(major_id="").status_code, 400)
        self.client.force_login(self.super_admin)
        self.assertEqual(self.save_product(seller_id=self.foreign.pk, major_id=self.ia.pk).status_code, 201)

    def test_program_and_major_filters_intersect(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse("admin_products_page"), {"view": "inventory", "program": self.btled.pk, "major": self.he.pk})
        self.assertEqual([row["product_id"] for row in response.context["inventory_page"]], [self.local.pk])
        mismatch = self.client.get(reverse("admin_products_page"), {"view": "inventory", "program": self.bsit.pk, "major": self.he.pk})
        self.assertEqual(mismatch.context["inventory_summary"]["total"], 0)

    def test_report_preview_export_and_analytics_remain_in_scope(self):
        self.order(self.local, "HE-PAID")
        self.order(self.other, "IA-PAID")
        for report_type in ("sales", "orders", "products", "low_stock"):
            report = build_report(report_type, user=self.admin)
            self.assertNotIn("IA Private Product", json.dumps(report))
        preview = self.client.get(reverse("admin_report_preview"), {"report_type": "products"})
        self.assertEqual(preview.status_code, 200)
        self.assertNotContains(preview, "IA Private Product")
        export = self.client.get(reverse("admin_report_download"), {"report_type": "products", "format": "csv"})
        self.assertEqual(export.status_code, 200)
        self.assertNotContains(export, "IA Private Product")
        analytics = build_marketplace_analytics({"period": "30"}, user=self.admin)
        self.assertEqual(analytics["kpis"]["sales"], "10.00")
        self.assertEqual(analytics["kpis"]["completed_orders"], 1)
        self.assertNotIn("IA Private Product", json.dumps(analytics, default=str))
        page = self.client.get(reverse("admin_marketplace_analytics_page"))
        self.assertEqual(page.context["analytics"]["kpis"]["completed_orders"], 1)

    def test_seller_notifications_and_review_actions_are_scoped(self):
        own = SellerRequest.objects.create(user=self.seller, student_id="HE001", status="pending")
        foreign = SellerRequest.objects.create(user=self.foreign, student_id="IA001", status="pending")
        context = get_notification_context(user=self.admin)
        self.assertEqual(context["pending_seller_requests"], 1)
        self.assertEqual([r.pk for r in context["seller_requests"]], [own.pk])
        response = self.client.post(reverse("marketplace_approve_seller_request", args=[foreign.pk]))
        self.assertEqual(response.status_code, 404)

    def test_seller_submission_keeps_actual_assigned_program(self):
        SellerRequest.objects.create(user=self.seller, student_id=self.seller.username,
            full_name="Approved Seller", product_type="Supplies", status="approved")
        self.client.force_login(self.seller)
        response = self.client.post(reverse("seller_submit_product"), json.dumps({"name": "Seller item", "price": 10, "stock": 5}), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        payload = response.json()["product"]
        self.assertEqual((payload["program_id"], payload["major_id"]), (self.btled.pk, self.he.pk))

    def test_stock_history_and_sku_are_shared_between_detail_and_inventory(self):
        self.local.stock = 4
        self.local.save(update_fields=["stock", "updated_at"])
        sku = self.local.inventory_skus.get(variant_name="")
        payload = serialize_product(self.local, include_inventory=True)
        row = build_inventory_table([self.local])[0]
        page = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_item": sku.pk})
        detail = page.context["inventory_detail"]
        self.assertEqual(payload["sku"], row["sku"])
        self.assertEqual(payload["inventory"]["available"], row["available"])
        self.assertEqual(payload["stock_movements"][0]["quantity"], detail["movements"][0]["quantity"])
        self.assertEqual(payload["stock_movements"][0]["reference"], detail["movements"][0]["reference"])

    def test_archive_restore_preserve_orders_skus_movements_and_counts(self):
        self.order(self.local, "PRESERVED-ORDER")
        before = (self.local.stock, list(self.local.inventory_skus.values()), list(InventoryStockMovement.objects.values()), MarketplaceOrder.objects.count())
        total = self.client.get(reverse("admin_products_page")).context["product_stats"]["total"]
        for route, archived in (("admin_archive_product", True), ("admin_restore_product", False)):
            response = self.client.post(reverse(route, args=[self.local.pk]))
            self.assertEqual(response.status_code, 200)
            self.local.refresh_from_db()
            self.assertEqual(self.local.is_archived, archived)
            self.assertEqual((self.local.stock, list(self.local.inventory_skus.values()), list(InventoryStockMovement.objects.values()), MarketplaceOrder.objects.count()), before)
            page = self.client.get(reverse("admin_products_page"))
            self.assertEqual(page.context["product_stats"]["total"], total)
            self.assertEqual(page.context["product_stats"]["low_stock"], 0 if archived else 1)
            inventory = self.client.get(reverse("admin_products_page"), {"view": "inventory"})
            self.assertEqual(inventory.context["inventory_summary"]["total"], 0 if archived else 1)

    def test_export_isolated_catalog_and_inventory_for_browser_review(self):
        directory = os.environ.get("CATALOG_REVIEW_DIR")
        if not directory:
            return
        self.client.force_login(self.super_admin)
        Product.objects.create(seller=self.seller, name="Archived HE Product", department=self.btled, major=self.he,
                               price=10, stock=2, is_archived=True, approval_status="pending")
        owner = User.objects.create_user(username="bsit-catalog-owner", department=self.bsit)
        variant = Product.objects.create(seller=owner, name="Test Uniform", department=self.bsit,
            price=250, stock=16, approval_status="approved", customization_enabled=True,
            customization_options=[{"name":"Size", "options":[{"name":"Small", "stock":10, "low_stock_threshold":3},
                                    {"name":"Medium", "stock":5, "low_stock_threshold":2},
                                    {"name":"Large", "stock":1, "low_stock_threshold":2}]}])
        for seller in (self.seller, self.foreign, owner):
            SellerRequest.objects.create(user=seller, student_id=f"CATALOG-{seller.pk}", status="approved")
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        (path / "products.html").write_bytes(self.client.get(reverse("admin_products_page")).content)
        (path / "inventory-filters.html").write_bytes(self.client.get(reverse("admin_products_page"), {"view":"inventory"}).content)
        (path / "catalog.json").write_text(json.dumps([serialize_product(p, include_inventory=True) for p in Product.objects.all()]), encoding="utf-8")


class ProgramMasterMigrationTests(TransactionTestCase):
    available_apps = ["accounts", "api", "django.contrib.auth", "django.contrib.contenttypes"]

    def test_known_legacy_majors_are_normalized_without_stock_or_history_changes(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("api", "0033_inventory_sku_and_movements"), ("accounts", "0023_remove_domain_backup_permissions")])
        try:
            old = executor.loader.project_state([("api", "0033_inventory_sku_and_movements"), ("accounts", "0023_remove_domain_backup_permissions")]).apps
            OldDept, OldUser, OldProduct = old.get_model("accounts", "Department"), old.get_model("accounts", "User"), old.get_model("api", "Product")
            with connection.cursor() as cursor:
                columns = {row.name for row in connection.introspection.get_table_description(cursor, "campushub_accounts_user")}
                if "email_verified" in columns:
                    cursor.execute('ALTER TABLE campushub_accounts_user ALTER COLUMN email_verified SET DEFAULT FALSE')
            dept = OldDept.objects.create(code="BTLED-HE", name="Home Economics")
            owner = OldUser.objects.create(username="legacy-owner", department_id=dept.pk)
            product = OldProduct.objects.create(seller_id=owner.pk, name="Legacy", price=10, stock=7, department_id=dept.pk)
            unassigned = OldProduct.objects.create(seller_id=owner.pk, name="Owner fallback", price=10, stock=2)
            before = list(OldProduct.objects.values("pk", "stock", "customization_options", "seller_id"))
            MigrationExecutor(connection).migrate([("api", "0035_program_master_data")])
            self.assertEqual(list(Product.objects.values("pk", "stock", "customization_options", "seller_id")), before)
            migrated = MigrationExecutor(connection).loader.project_state([("api", "0035_program_master_data")]).apps
            owner = migrated.get_model("accounts", "User").objects.get(pk=owner.pk)
            self.assertEqual((owner.department.code, owner.major.code), ("BTLED", "HE"))
            for item in migrated.get_model("api", "Product").objects.filter(pk__in=[product.pk, unassigned.pk]):
                self.assertEqual((item.department_id, item.major_id), (owner.department_id, owner.major_id))
            self.assertTrue(Department.objects.filter(pk=dept.pk, is_program=False).exists())
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
