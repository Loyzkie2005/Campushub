"""Saved warning levels across creation, reservations, variants and monitoring."""
import json
import os
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, Department
from api.models import Product
from api.views import serialize_product
from modules.marketplace.services.inventory import (
    get_product_inventory_snapshot, get_product_quantity_status,
    iter_product_low_stock, low_stock_inventory_rows, low_stock_threshold,
)
from modules.marketplace.services.analytics import build_marketplace_analytics
from modules.reports.dashboard_attention import inventory_attention_counts
from modules.reports.dashboard_low_stock import build_low_stock_card
from modules.reports.reporting import build_report


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"], CAMPUSHUB_LOW_STOCK_THRESHOLD=7)
class ProductLowStockThresholdTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name":"Computing Program", "is_program":True})
        cls.admin = User.objects.create_superuser(username="threshold-admin", password="CampusHub1!", role="Super Admin", department=program)

    def setUp(self):
        self.client.force_login(self.admin)

    def save(self, **changes):
        payload = {"name": "Threshold item", "category": "Clothing", "price": "250", "stock": 10,
                   "low_stock_threshold": 3}
        payload.update(changes)
        return self.client.post(reverse("admin_save_product"), json.dumps(payload), content_type="application/json")

    def product(self, **changes):
        payload = {"seller": self.admin, "name": "Stored threshold", "price": 10,
                   "stock": 10, "low_stock_threshold": 3, "approval_status": Product.STATUS_APPROVED}
        payload.update(changes)
        return Product.objects.create(**payload)

    def test_create_persists_threshold_and_all_status_boundaries(self):
        response = self.save()
        self.assertEqual(response.status_code, 201)
        product = Product.objects.get(pk=response.json()["product"]["id"])
        self.assertEqual(product.low_stock_threshold, 3)
        self.assertEqual(response.json()["product"]["low_stock_threshold"], 3)
        for available in range(10, -1, -1):
            product.stock = available
            expected = "out_of_stock" if available == 0 else "low_stock" if available <= 3 else "in_stock"
            with self.subTest(available=available):
                self.assertEqual(product.get_inventory_status(), expected)
                self.assertEqual(get_product_quantity_status(product), expected)
                self.assertEqual(bool(list(iter_product_low_stock(product))), 0 < available <= 3)

    def test_creation_rejects_invalid_explicit_thresholds_without_writing_records(self):
        for value in (-1, "", "2.5", 2.5, True, None, 10, 11):
            with self.subTest(threshold=value):
                response = self.save(low_stock_threshold=value)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["field"], "low_stock_threshold")
        self.assertEqual(Product.objects.count(), 0)
        response = self.save(stock=5, low_stock_threshold=10)
        self.assertEqual(response.json()["error"], "Low Stock Threshold must be lower than the initial stock quantity.")

    def test_zero_threshold_and_zero_stock_are_safe(self):
        response = self.save(stock=0, low_stock_threshold=0)
        self.assertEqual(response.status_code, 201)
        product = Product.objects.get(pk=response.json()["product"]["id"])
        self.assertEqual(low_stock_threshold(product), 0)
        self.assertEqual(product.get_inventory_status(), "out_of_stock")
        product.stock = 1
        product.save(update_fields=["stock"])
        self.assertEqual(product.get_inventory_status(), "in_stock")
        self.assertEqual(low_stock_inventory_rows(Product.objects.all()), [])

    def test_reserved_stock_uses_saved_level_without_second_subtraction(self):
        product = self.product()
        response = self.client.post(reverse("marketplace_orders"), json.dumps({
            "product_id": product.pk, "buyer_user_id": self.admin.pk, "quantity": 7,
        }), content_type="application/json")
        self.assertEqual(response.status_code, 201)
        product.refresh_from_db()
        inventory = get_product_inventory_snapshot(product)
        assert inventory is not None, "Expected an inventory snapshot for the valid reserved-stock fixture."
        self.assertEqual((inventory["on_hand"], inventory["reserved"], inventory["available"]), (10, 7, 3))
        self.assertEqual((inventory["low_stock_threshold"], inventory["status"]), (3, "low_stock"))
        self.assertEqual(build_low_stock_card(today=timezone.localdate())["products"][0]["threshold"], 3)

    def test_variants_store_separate_levels_and_ignore_parent_level(self):
        groups = [{"name": "Size", "required": True, "options": [
            {"name": "Medium", "stock": 10, "low_stock_threshold": 3},
            {"name": "Large", "stock": 5, "low_stock_threshold": 2}]}]
        response = self.save(customization_enabled=True, customization_options=groups, low_stock_threshold=99, stock=999)
        self.assertEqual(response.status_code, 201)
        product = Product.objects.get(pk=response.json()["product"]["id"])
        self.assertIsNone(product.low_stock_threshold)
        self.assertEqual(product.get_total_stock(), 15)
        self.assertEqual([o["low_stock_threshold"] for o in product.customization_options[0]["options"]], [3, 2])
        product.customization_options[0]["options"][0]["stock"] = 4
        product.customization_options[0]["options"][1]["stock"] = 3
        product.save(update_fields=["customization_options"])
        self.assertEqual(get_product_quantity_status(product), "in_stock")
        self.assertEqual(low_stock_inventory_rows(Product.objects.all()), [])
        product.customization_options[0]["options"][1]["stock"] = 2
        product.save(update_fields=["customization_options"])
        self.assertEqual(get_product_quantity_status(product), "low_stock")
        rows = low_stock_inventory_rows(Product.objects.all())
        self.assertEqual([(r["variant_name"], r["available"], r["threshold"]) for r in rows], [("Large", 2, 2)])
        inventory = get_product_inventory_snapshot(product)
        assert inventory is not None, "Expected an inventory snapshot for the valid variant fixture."
        self.assertIsNone(inventory["low_stock_threshold"])
        self.assertEqual([r["threshold"] for r in inventory["variant_thresholds"]], [3, 2])
        self.assertEqual(inventory_attention_counts(timezone.localdate())["low_stock_products"], 1)

    def test_variant_creation_validation_and_existing_low_stock_edit(self):
        bad = [{"name": "Size", "options": [{"name": "Large", "stock": 5, "low_stock_threshold": 5}]}]
        self.assertEqual(self.save(customization_enabled=True, customization_options=bad).status_code, 400)
        product = self.product(stock=1)
        self.assertEqual(self.save(id=product.pk, stock=1, low_stock_threshold=3).status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.low_stock_threshold, 3)
        self.assertEqual(product.get_inventory_status(), "low_stock")
        variant = self.product(customization_enabled=True, low_stock_threshold=None,
            customization_options=[{"name": "Size", "options": [{"name": "Medium", "stock": 1, "low_stock_threshold": 3}]}])
        old_client_options = [{"name": "Size", "options": [{"name": "Medium", "stock": 1}]}]
        response = self.save(id=variant.pk, customization_enabled=True, customization_options=old_client_options)
        self.assertEqual(response.status_code, 200)
        variant.refresh_from_db()
        self.assertEqual(variant.customization_options[0]["options"][0]["low_stock_threshold"], 3)

    def test_legacy_default_and_thresholds_reach_list_details_and_dashboard(self):
        legacy = self.product(stock=6, low_stock_threshold=None)
        normal = self.product(name="Quiet stock", stock=4, low_stock_threshold=3)
        low = self.product(name="Low stock", stock=2, low_stock_threshold=2)
        self.assertEqual(low_stock_threshold(legacy), 7)
        with override_settings(CAMPUSHUB_LOW_STOCK_THRESHOLD=5):
            self.assertEqual(legacy.get_inventory_status(), "in_stock")
            self.assertEqual(low_stock_threshold(normal), 3)
        page = self.client.get(reverse("admin_products_page"))
        views = {p.pk: p for p in page.context["seller_products"]}
        self.assertEqual(views[normal.pk].admin_quantity_status, "in_stock")
        self.assertEqual(views[low.pk].admin_quantity_status, "low_stock")
        self.assertContains(page, 'id="productLowStockThreshold"')
        self.assertContains(page, "You will be alerted when available stock reaches this amount or lower.")
        self.assertContains(page, 'data-low-stock-threshold="3"')
        self.assertContains(page, "Threshold: 3")
        payload = self.client.get(reverse("seller_products_monitor"), {"product_id": low.pk}).json()["products"][0]
        self.assertEqual(payload["inventory"]["low_stock_threshold"], 2)
        card = build_low_stock_card(today=timezone.localdate())
        self.assertNotIn(normal.pk, [r["product_id"] for r in card["products"]])
        self.assertEqual(inventory_attention_counts(timezone.localdate())["low_stock_products"], 2)
        directory = os.environ.get("PRODUCT_THRESHOLDS_REVIEW_DIR")
        if directory:
            variant = self.product(name="Sizes", customization_enabled=True, low_stock_threshold=None,
                customization_options=[{"name": "Size", "required": True, "options": [
                    {"name": "Medium", "stock": 4, "low_stock_threshold": 3},
                    {"name": "Large", "stock": 2, "low_stock_threshold": 2}]}])
            page = self.client.get(reverse("admin_products_page"))
            target = Path(directory)
            target.mkdir(parents=True, exist_ok=True)
            (target / "products.html").write_bytes(page.content)
            (target / "products.json").write_text(json.dumps([
                serialize_product(p, include_inventory=True) for p in page.context["seller_products"]]), encoding="utf-8")

    def test_bundle_submission_cannot_create_standalone_inventory(self):
        response = self.save(product_type="bundle")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.objects.count(), 0)

    def test_dashboard_shortlist_ranks_relative_to_each_saved_threshold(self):
        for index in range(6):
            self.product(name=f"Near level {index}", stock=1, low_stock_threshold=1)
        critical = self.product(name="Most depleted", stock=8, low_stock_threshold=80)
        rows = low_stock_inventory_rows(Product.objects.all(), limit=5)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["product"].pk, critical.pk)
        self.assertEqual(rows[0]["threshold"], 80)

    def test_analytics_and_report_use_each_level_and_parent_variant_summary(self):
        normal = self.product(name="Normal at four", stock=4, low_stock_threshold=3)
        low = self.product(name="Low at six", stock=6, low_stock_threshold=7)
        variant = self.product(name="One low option", customization_enabled=True,
            customization_options=[{"name": "Size", "options": [
                {"name": "Medium", "stock": 0, "low_stock_threshold": 3},
                {"name": "Large", "stock": 2, "low_stock_threshold": 2}]}])
        analytics = build_marketplace_analytics({"period": "7"}, today=timezone.localdate())
        rows = {row["product_id"]: row for row in analytics["inventory"]["all_rows"]}
        self.assertEqual(rows[normal.pk]["state"], "Healthy")
        self.assertEqual(rows[low.pk]["state"], "Low Stock")
        self.assertEqual(rows[variant.pk]["state"], "Low Stock")
        self.assertEqual(analytics["inventory"]["summary"]["low_stock"], 2)
        report = build_report("low_stock")
        self.assertEqual({row["Product"] for row in report["rows"]}, {low.name, variant.name})
        self.assertTrue(all(row["Inventory Status"] == "Low Stock" for row in report["rows"]))
        self.assertEqual(next(row["Stock"] for row in report["rows"] if row["Product"] == variant.name), 2)
