"""Real inventory, variant-level monitoring and existing navigation integration."""
from datetime import date, timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError, connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts import tests as fixtures
from api.models import Product
from modules.marketplace.services.inventory import adjust_product_stock, low_stock_inventory_rows
from .dashboard_low_stock import build_low_stock_card


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DashboardLowStockTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 5)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        Product.objects.update(stock=100, customization_options=[])
        self.client.force_login(self.super_admin)

    def product(self, name="Monitoring product", stock=3, **fields):
        return Product.objects.create(seller=self.seller, name=name, stock=stock, price=10,
                                      approval_status=Product.STATUS_APPROVED, **fields)

    def snapshot(self):
        return build_low_stock_card(today=self.today)

    def test_threshold_boundaries_and_out_of_stock_are_distinct(self):
        with override_settings(CAMPUSHUB_LOW_STOCK_THRESHOLD=20):
            expected = [self.product(f"Stock {value}", stock=value).pk for value in (10, 20)]
            for stock in (21, 0):
                self.product(f"Excluded {stock}", stock=stock)
            rows = self.snapshot()["products"]
            self.assertEqual([row["product_id"] for row in rows], expected)
            self.assertEqual([row["available"] for row in rows], [10, 20])
            self.assertTrue(all(row["threshold"] == 20 for row in rows))

    def test_live_setting_is_reused_without_new_model_fields(self):
        self.product(stock=4)
        self.assertEqual(self.snapshot()["products"][0]["threshold"], 5)
        with override_settings(CAMPUSHUB_LOW_STOCK_THRESHOLD=2):
            self.assertEqual(self.snapshot()["products"], [])

    def test_combined_alerts_prioritize_depleted_stock_and_reuse_variant_rules(self):
        low = self.product('Low positive stock', stock=1)
        zero = self.product('Depleted stock', stock=0)
        self.product('Expired depleted', stock=0, category='Snacks', expiry_date=self.today - timedelta(days=1))
        self.product('Archived depleted', stock=0, is_archived=True)
        variant = self.product('Variant inventory', stock=99, customization_enabled=True,
            customization_options=[{'name': 'Size', 'options': [
                {'name': 'Small', 'stock': 0}, {'name': 'Large', 'stock': 3}]}])
        result = build_low_stock_card(today=self.today, include_out_of_stock=True)
        self.assertEqual([row['status'] for row in result['products']],
                         ['out_of_stock', 'out_of_stock', 'low_stock', 'low_stock'])
        self.assertEqual([row['product_id'] for row in result['products']], [zero.pk, variant.pk, low.pk, variant.pk])
        self.assertEqual(result['products'][1]['variant_key'], '0:0')
        self.assertEqual(result['view_all_url'], reverse('admin_products_page') + '?view=inventory')
        zero.refresh_from_db()
        self.assertEqual(zero.stock, 0)
        self.assertNotIn(zero.pk, [row['product_id'] for row in self.snapshot()['products']])

    def test_depleted_zero_threshold_remains_first_in_bounded_shortlist(self):
        for index in range(6):
            self.product(f'Positive low {index}', stock=1)
        depleted = self.product('Zero threshold depleted', stock=0, low_stock_threshold=0)
        result = build_low_stock_card(today=self.today, include_out_of_stock=True)
        self.assertEqual(len(result['products']), 5)
        self.assertEqual(result['products'][0]['product_id'], depleted.pk)

    def test_reservations_are_not_subtracted_twice_and_restore_is_visible(self):
        product = self.product(stock=10)
        adjust_product_stock(product, [], 7)
        product.save(update_fields=["stock"])
        self.assertEqual(self.snapshot()["products"][0]["available"], 3)
        adjust_product_stock(product, [], 7, restore=True)
        product.save(update_fields=["stock"])
        self.assertEqual(self.snapshot()["products"], [])

    def test_only_low_variants_appear_even_if_parent_is_partial(self):
        product = self.product(name="Campus Hoodie", stock=999, customization_enabled=True,
                               customization_options=[{"name": "Size", "options": [
                                   {"name": "Medium", "stock": 2}, {"name": "Large", "stock": 20},
                                   {"name": "Small", "stock": 0},
                               ]}])
        rows = self.snapshot()["products"]
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["product_id"], rows[0]["variant_name"], rows[0]["available"]),
                         (product.pk, "Medium", 2))
        page = self.client.get(reverse("admin_products_page"), {"inventory_status": "low_stock"})
        product_view = next(p for p in page.context["seller_products"] if p.pk == product.pk)
        self.assertTrue(product_view.admin_has_low_stock)
        # Existing priority marks the parent Out of Stock if any option is zero.
        # The Low Stock filter must still find its separate positive low option.
        self.assertEqual(product_view.admin_inventory_status, "partially_available")
        self.assertEqual(page.context["product_stats"]["low_stock"], 1)

    def test_expired_and_archived_rows_are_excluded(self):
        self.product("Archived", is_archived=True)
        self.product("Expired", category="Snacks", expiry_date=self.today - timedelta(days=1))
        self.product("Variant expiry", category="Snacks", customization_enabled=True,
                     customization_options=[{"options": [{"name": "Expired", "stock": 2,
                                         "expiry_date": (self.today - timedelta(days=1)).isoformat()},
                                         {"name": "Fresh", "stock": 4}]}])
        rows = self.snapshot()["products"]
        self.assertEqual([row["variant_name"] for row in rows], ["Fresh"])

    def test_shortlist_is_five_most_critical_rows_in_stable_order(self):
        products = [self.product(f"Item {index}", stock=stock)
                    for index, stock in enumerate((5, 1, 4, 2, 3, 1, 4))]
        rows = self.snapshot()["products"]
        self.assertEqual([row["available"] for row in rows], [1, 1, 2, 3, 4])
        self.assertEqual([row["product_id"] for row in rows[:2]], [products[1].pk, products[5].pk])

    def test_variant_queries_are_bounded_and_do_not_load_sellers(self):
        for index in range(40):
            self.product(f"Variant {index}", customization_options=[{"options": [{"stock": 2}]}])
        with CaptureQueriesContext(connection) as queries:
            rows = low_stock_inventory_rows(Product.objects.all(), today=self.today)
        self.assertEqual(len(queries), 2)
        self.assertEqual(len(rows), 5)
        self.assertNotIn('"campushub_orders"', " ".join(q["sql"] for q in queries))

    def test_card_links_real_images_and_product_detail(self):
        product = self.product(image_url="/media/real-product.jpg")
        snapshot = self.snapshot()
        row = snapshot["products"][0]
        self.assertEqual(snapshot["view_all_url"], reverse("admin_products_page") + "?view=inventory&inventory_status=low_stock")
        self.assertEqual(row["url"], reverse("admin_products_page") + f"?view=inventory&product_id={product.pk}")
        self.assertEqual(row["image_url"], reverse("product_image", args=[product.pk]))
        self.assertEqual(self.client.get(row["url"]).status_code, 200)

    def test_inventory_failure_is_explicit_not_healthy_empty(self):
        with patch("modules.reports.dashboard_low_stock.low_stock_inventory_rows", side_effect=DatabaseError("unavailable")):
            with self.assertLogs("modules.reports.dashboard_low_stock", level="ERROR"):
                self.assertEqual(self.snapshot()["state"], "error")
        with patch("modules.reports.dashboard_low_stock.low_stock_inventory_rows", side_effect=DatabaseError("unavailable")), \
                patch("modules.reports.dashboard_low_stock.logger.exception"):
            response = self.client.get(reverse("admin_dashboard_page"))
            self.assertContains(response, "Unable to load inventory alerts.")
            self.assertContains(response, 'data-low-stock-content hidden')

    def test_snapshot_is_current_for_all_date_filters_and_refreshes(self):
        product = self.product(stock=2)
        url = reverse("admin_dashboard_api")
        for period in ("today", "last_30_days", "this_year"):
            payload = self.client.get(url, {"period": period}).json()
            self.assertEqual(payload["low_stock"]["products"][0]["available"], 2)
        Product.objects.filter(pk=product.pk).update(stock=4)
        self.assertEqual(self.client.get(url).json()["low_stock"]["products"][0]["available"], 4)

    def test_dashboard_endpoint_enforces_super_admin_access(self):
        url = reverse("admin_dashboard_api")
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 401)
        for user in (self.marketplace_admin, self.facilities_admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_empty_and_populated_markup_and_review_artifacts(self):
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        for state in ("empty", "populated"):
            if state == "populated":
                for index, stock in enumerate((1, 2, 3, 4, 5)):
                    self.product(f"Test inventory item {index + 1}", stock=stock)
            page = self.client.get(reverse("admin_dashboard_page"))
            self.assertContains(page, "Products requiring stock attention will appear here.")
            self.assertContains(page, 'data-low-stock-card', count=1)
            self.assertContains(page, 'id="lowStockSlot"', count=1)
            html = page.content.decode("utf-8")
            self.assertLess(html.index('id="lowStockSlot"'), html.index('id="facilitiesOverviewTitle"'))
            self.assertContains(page, '>Available</th>')
            self.assertContains(page, '>Status</th>')
            self.assertContains(page, 'view=inventory')
            self.assertContains(page, 'id="lowStockRetry"')
            if directory:
                path = Path(directory)
                path.mkdir(parents=True, exist_ok=True)
                (path / f"low-stock-{state}.html").write_bytes(page.content)
                (path / f"low-stock-{state}.json").write_text(json.dumps(self.client.get(reverse("admin_dashboard_api")).json()), encoding="utf-8")
                (path / "low-stock-products.html").write_bytes(self.client.get(reverse("admin_products_page"), {"inventory_status": "low_stock"}).content)
