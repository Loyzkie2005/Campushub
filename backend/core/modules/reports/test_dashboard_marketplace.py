"""Selected-period marketplace ranking, category performance and chart layout."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.db import connection
from django.test import override_settings
from django.template.loader import render_to_string
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from api.models import MarketplaceOrder, Product
from .dashboard_marketplace import recent_marketplace_orders, sales_by_product_category, top_selling_products

TEST_PRODUCT_IMAGE = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII="


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DashboardMarketplaceTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        MarketplaceOrder.objects.all().delete()
        self.client.force_login(self.super_admin)

    def order(self, product=None, quantity=1, amount="100", day=None, **fields):
        product = product or self.prod_approved
        with timezone.override("Asia/Manila"):
            stamp = timezone.make_aware(datetime.combine(day or self.today, time(12)))
        return MarketplaceOrder.objects.create(
            product=product, product_name=fields.pop("product_name", product.name),
            quantity=quantity, unit_price=Decimal(amount) / quantity, total_price=amount,
            status=fields.pop("status", MarketplaceOrder.STATUS_COMPLETED),
            payment_status=fields.pop("payment_status", MarketplaceOrder.PAYMENT_PAID),
            completed_at=stamp, paid_at=stamp, **fields,
        )

    def api(self, params=None):
        with patch("django.utils.timezone.localdate", return_value=self.today):
            response = self.client.get(reverse("admin_dashboard_api"), params or {})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_top_five_groups_parent_variants_and_sorts_quantity_then_revenue(self):
        self.order(quantity=4, amount="120", product_name="Old lanyard name", option="Blue")
        self.order(quantity=3, amount="90", option="Gold")
        for index, (quantity, amount) in enumerate(((8, "80"), (7, "500"), (6, "600"), (5, "400"), (4, "900"), (3, "500"))):
            product = Product.objects.create(seller=self.seller, name=f"Product {index}", price=1)
            self.order(product, quantity, amount)
        data = self.api({"period": "today"})["marketplace"]
        ranked = data["top_products"]
        self.assertEqual(len(ranked), 5)
        self.assertEqual([row["rank"] for row in ranked], [1, 2, 3, 4, 5])
        self.assertEqual([row["units_sold"] for row in ranked], [8, 7, 7, 6, 5])
        self.assertEqual(ranked[1]["sales"], "500.00")
        self.assertEqual(ranked[2]["id"], self.prod_approved.pk)
        self.assertEqual(ranked[2]["product_name"], self.prod_approved.name)
        self.assertEqual(ranked[2]["sales"], "210.00")
        self.assertEqual(data["top_selling_product"], ranked[0])

    def test_sales_overview_system_preview_values_and_grouping(self):
        """Visible preview fixtures live only in the isolated Django test database."""
        self.today = date(2026, 10, 5)
        sample_products = [
            (Product.objects.create(seller=self.seller, name=name, category=category, price="100"), quantity)
            for name, category, quantity in (
                ("CampusHub Hoodie", "Apparel & Uniforms", 5),
                ("Iced Spanish Latte", "Food & Beverages", 4),
                ("Spiral Notebook", "School Supplies", 3),
                ("Canvas Tote Bag", "Accessories", 2),
                ("Basketball", "Sports", 1),
                ("USB Flash Drive", "Electronics", 1),
            )
        ]
        transaction_index = 0
        daily_cases = ((2, "175"), (3, "175"), (0, "0"), (4, "200"), (2, "225"), (5, "225"), (2, "325"))
        for offset, (count, amount) in enumerate(daily_cases):
            day = self.today - timedelta(days=6 - offset)
            for _ in range(count):
                product, quantity = sample_products[transaction_index % len(sample_products)]
                self.order(product, quantity=quantity, amount=amount, day=day,
                           category=product.category, buyer_name="Marketplace analytics test customer")
                transaction_index += 1
        for _ in range(9):
            self.order(amount="100", day=self.today - timedelta(days=8), buyer_name="Previous-period test customer")
        self.order(amount="9999", status="completed", payment_status="unpaid")
        self.order(amount="8888", status="pending", payment_status="paid")
        directory = os.environ.get("SALES_SYSTEM_TEST_DIR")
        sample_markup = render_to_string("dashboard/partials/sales_sample_data.html")
        sample = json.loads(sample_markup.split('id="salesSampleData">', 1)[1].split('</script>', 1)[0])
        for state in ("populated", "empty"):
            for grouping in ("daily", "weekly", "monthly"):
                params = {"period": "last_7_days", "grouping": grouping}
                if state == "empty":
                    params.update(period="custom", start_date="2026-09-01", end_date="2026-09-07")
                payload = self.api(params)
                sales = payload["marketplace"]
                values = {metric["key"]: metric["value"] for metric in sales["sales_overview"]["metrics"]}
                self.assertEqual(values, {"sales": "3,900.00", "orders": "18", "average": "216.67"} if state == "populated" else {"sales": "0.00", "orders": "0", "average": "0.00"})
                self.assertEqual(sum(sales["sales_trend"]["sales"]), 3900 if state == "populated" else 0)
                self.assertEqual(sum(sales["sales_trend"]["orders"]), 18 if state == "populated" else 0)
                self.assertEqual(sales["sales_trend"]["grouping"], grouping)
                if state == "populated" and grouping == "daily":
                    self.assertEqual(sales["sales_trend"]["sales"], [350, 525, 0, 800, 450, 1125, 650])
                    self.assertEqual(payload["kpis"]["marketplace_revenue"]["previous_value"], 900)
                if state == "populated":
                    self.assertEqual(len(sales["top_products"]), 5)
                    self.assertEqual([product["units_sold"] for product in sales["top_products"]], [15, 12, 9, 6, 3])
                    self.assertEqual(len(sales["product_categories"]["categories"]), 6)
                    self.assertEqual(sales["product_categories"]["total_sales"], "3,900.00")
                    self.assertEqual(sample["trends"][grouping], sales["sales_trend"])
                    self.assertEqual(sample["metrics"], sales["sales_overview"]["metrics"])
                    self.assertEqual(sample["top_products"], [
                        {key: product[key] for key in ("rank", "product_name", "category", "units_sold", "sales")}
                        for product in sales["top_products"]
                    ])
                    self.assertEqual(sample["product_categories"], sales["product_categories"])
                if directory:
                    path = Path(directory)
                    path.mkdir(parents=True, exist_ok=True)
                    with patch("django.utils.timezone.localdate", return_value=self.today):
                        page = self.client.get(reverse("admin_dashboard_page"), params)
                    self.assertEqual(page.status_code, 200)
                    self.assertNotContains(page, 'data-sales-sample-toggle')
                    self.assertNotContains(page, 'id="salesSampleData"')
                    (path / f"{state}-{grouping}.source.html").write_bytes(page.content)
                    (path / f"{state}-{grouping}.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_recent_orders_are_newest_snapshot_with_separate_payment_status(self):
        MarketplaceOrder.objects.all().delete()
        orders = []
        for index in range(8):
            order = self.order(quantity=index + 1, amount=str((index + 1) * 10),
                               status="pending" if index == 7 else "completed",
                               payment_status="unpaid" if index == 7 else "paid",
                               buyer_name=f"Customer {index}")
            MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=timezone.make_aware(datetime.combine(self.today - timedelta(days=8 - index), time(12))))
            orders.append(order)
        data = self.api({"period": "today"})
        recent = data["operations"]["recent_orders"]
        self.assertEqual(len(recent), 5)
        self.assertEqual([row["id"] for row in recent], [order.pk for order in reversed(orders[3:])])
        self.assertEqual(recent[0]["status"], "Pending")
        self.assertEqual(recent[0]["payment_status"], "Unpaid")
        self.assertEqual(recent[1]["status"], "Completed")
        self.assertEqual(recent[1]["payment_status"], "Paid")
        self.assertEqual(recent[0]["quantity"], 8)
        self.assertEqual(recent[0]["item_count"], 8)
        self.assertEqual(recent[0]["seller_name"], self.prod_approved.owner.get_full_name() or self.prod_approved.owner.username)
        self.assertEqual(recent[0]["buyer_name"], "Customer 7")
        self.assertEqual(recent[0]['url'], reverse('admin_orders_page') + f'?order={orders[-1].pk}')
        linked = self.client.get(recent[0]['url'])
        self.assertEqual(linked.status_code, 200)
        self.assertContains(linked, f'data-order-id="{orders[-1].pk}"')
        self.assertEqual(recent, self.api({"period": "this_year", "booking_grouping": "monthly"})["operations"]["recent_orders"])
        directory = os.environ.get("RECENT_ORDERS_REVIEW_DIR")
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            with patch("django.utils.timezone.localdate", return_value=self.today):
                page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
            (target / "populated.html").write_bytes(page.content)
            (target / "populated.json").write_text(json.dumps(data), encoding="utf-8")
        MarketplaceOrder.objects.all().delete()
        self.assertEqual(self.api()["operations"]["recent_orders"], [])

    def test_recent_orders_use_saved_sellers_and_actual_web_mobile_owners_in_one_query(self):
        saved = self.order(seller_name="Seller recorded at checkout")
        web = self.order(seller_name="")
        mobile_product = Product.objects.create(mobile_seller=self.ch_user, name="Mobile seller item", price=100, stock=5)
        mobile = self.order(mobile_product, seller_name="")
        deleted = self.order(seller_name="Historical seller")
        missing = self.order(seller_name="")
        MarketplaceOrder.objects.filter(pk__in=[deleted.pk, missing.pk]).update(product=None)
        with CaptureQueriesContext(connection) as captured:
            rows = recent_marketplace_orders(MarketplaceOrder.objects.all(), limit=5)
        self.assertEqual(len(captured), 1)
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id[saved.pk]["seller_name"], "Seller recorded at checkout")
        self.assertEqual(by_id[web.pk]["seller_name"], self.prod_approved.owner.get_full_name() or self.prod_approved.owner.username)
        self.assertEqual(by_id[mobile.pk]["seller_name"], self.ch_user.get_full_name() or self.ch_user.username)
        self.assertEqual(by_id[deleted.pk]["seller_name"], "Historical seller")
        self.assertEqual(by_id[missing.pk]["seller_name"], "Not recorded")

    def test_recent_orders_count_legacy_units_without_assigning_a_primary_seller(self):
        legacy = self.order(quantity=9, seller_name="Primary seller only", customization={"items": [
            {"product_name": "First", "quantity": 3}, {"product_name": "Second", "quantity": "2"}]})
        incomplete = self.order(customization={"items": [{"quantity": 2}, {"quantity": "unknown"}]})
        invalid = self.order(customization={"items": [{"quantity": True}]})
        bundle = self.order(quantity=3, seller_name="Bundle seller", customization={
            "bundle_components": [{"quantity": 20}], "items": [{"quantity": 20}, {"quantity": 30}]})
        zero = self.order()
        MarketplaceOrder.objects.filter(pk=zero.pk).update(quantity=0)
        rows = {row["id"]: row for row in recent_marketplace_orders(MarketplaceOrder.objects.all(), limit=5)}
        self.assertEqual(rows[legacy.pk]["item_count"], 5)
        self.assertEqual(rows[legacy.pk]["seller_name"], "Not fully recorded")
        self.assertIsNone(rows[incomplete.pk]["item_count"])
        self.assertEqual(rows[incomplete.pk]["seller_name"], "Not fully recorded")
        self.assertIsNone(rows[invalid.pk]["item_count"])
        self.assertEqual(rows[bundle.pk]["item_count"], 3)
        self.assertEqual(rows[bundle.pk]["seller_name"], "Bundle seller")
        self.assertEqual(rows[zero.pk]["item_count"], 0)

    def test_analytics_operations_layout_and_removed_chart_tables(self):
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"))
        self.assertContains(page, 'id="marketplaceOverviewTitle"', count=1)
        self.assertContains(page, 'Average Order Value')
        self.assertNotContains(page, 'data-executive-sellers')
        marketplace_html = page.content.decode().split('aria-labelledby="marketplaceOverviewTitle">', 1)[1].split('class="marketplace-operations-row"', 1)[0]
        self.assertEqual(marketplace_html.count('<canvas '), 2)
        self.assertContains(page, 'id="topSellingProductsChart"', count=1)
        self.assertContains(page, '<th scope="col">Order Status</th>')
        self.assertContains(page, '<th scope="col">Order ID</th>')
        self.assertNotIn('View chart data', marketplace_html)
        self.assertNotContains(page, 'id="categorySalesCard"')
        html = page.content.decode()
        anchors = ['marketplaceOverviewTitle', 'recentOrdersSlot', 'lowStockSlot', 'facilitiesOverviewTitle', 'servicesOverviewTitle', 'recentActivitiesTitle']
        self.assertEqual([html.index('id="'+key+'"') for key in anchors], sorted(html.index('id="'+key+'"') for key in anchors))

    def test_category_sales_count_transactions_and_prefer_historical_category(self):
        self.order(quantity=8, category=" Clothing ", amount="800")
        self.order(quantity=2, category="Clothing", amount="200")
        self.order(self.prod_low, quantity=1, category="Sports", amount="100")
        self.order(self.prod_low, quantity=100, category="Sports", amount="999", payment_status="unpaid")
        Product.objects.all().update(category="Recategorized", is_archived=True)
        distribution = self.api({"period": "today"})["marketplace"]["product_categories"]
        self.assertFalse(distribution["is_snapshot"])
        self.assertEqual(distribution["share_basis"], "completed_paid_sales_amount")
        self.assertEqual(distribution["total_sales"], "1,100.00")
        self.assertEqual(distribution["total"], 3)
        self.assertEqual([{key: value for key, value in category.items() if key != "chart"} for category in distribution["categories"]], [
            {"name": "Clothing", "count": 2, "units_sold": 10, "sales": "1,000.00", "percentage": 90.9},
            {"name": "Sports", "count": 1, "units_sold": 1, "sales": "100.00", "percentage": 9.1},
        ])

    def test_category_donut_ranks_revenue_instead_of_order_count(self):
        self.order(category="Frequent", amount="10")
        self.order(category="Frequent", amount="10")
        self.order(self.prod_low, category="High revenue", amount="80")
        distribution = self.api({"period": "today"})["marketplace"]["product_categories"]
        self.assertEqual(distribution["total_sales"], "100.00")
        self.assertEqual([(row["name"], row["percentage"]) for row in distribution["categories"]],
                         [("High revenue", 80.0), ("Frequent", 20.0)])
        self.assertAlmostEqual(sum(row["chart"]["share"] for row in distribution["categories"]), 100)
        self.assertEqual(distribution["categories"][1]["chart"]["offset"], -80)

    def test_zero_value_category_orders_do_not_create_fake_donut_segments(self):
        self.order(category="Free item", amount="0")
        distribution = self.api({"period": "today"})["marketplace"]["product_categories"]
        self.assertEqual(distribution["total"], 1)
        self.assertEqual(distribution["total_sales"], "0.00")
        self.assertEqual(distribution["categories"][0]["percentage"], 0)
        self.assertEqual(distribution["categories"][0]["chart"]["share"], 0)
        self.write_category_review("zero")

    def write_category_review(self, state):
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        if not directory:
            return
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
        Path(directory).mkdir(parents=True, exist_ok=True)
        Path(directory, f"category-{state}.html").write_bytes(page.content)
        Path(directory, f"category-{state}.json").write_text(json.dumps(self.api({"period": "today"})), encoding="utf-8")

    def test_category_card_renders_six_real_sales_rows_and_accessible_donut(self):
        samples = [("Food & Beverages", "8900"), ("School Supplies", "5590"),
                   ("Apparel & Uniforms", "4580"), ("Accessories", "3050"),
                   ("Electronics", "2030"), ("Others", "1280")]
        for category, amount in samples:
            self.order(category=category, amount=amount)
        distribution = self.api({"period": "today"})["marketplace"]["product_categories"]
        self.assertEqual(distribution["total_sales"], "25,430.00")
        self.assertEqual(len(distribution["categories"]), 6)
        self.assertAlmostEqual(sum(row["chart"]["share"] for row in distribution["categories"]), 100, places=5)
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_marketplace_analytics_page"), {"period": "custom", "date_from": self.today.isoformat(), "date_to": self.today.isoformat()})
        self.assertContains(page, 'id="marketplaceCategoryChartData"')
        self.assertContains(page, 'Sales by Category')
        self.assertContains(page, 'Food &amp; Beverages')
        self.assertEqual(len(page.context['analytics']['category_sales']), 6)
        self.assertEqual(page.context['analytics']['category_sales'][0]['percent'], 35.0)
        self.assertContains(page, "25,430.00")
        self.write_category_review("six")

    def test_invalid_statuses_cannot_enter_any_sales_summary(self):
        self.order(quantity=2, category="Valid", amount="150")
        for status, payment in (("pending", "paid"), ("processing", "paid"), ("ready_for_pickup", "paid"), ("ready_for_pickup", "unpaid"), ("cancelled", "paid"), ("completed", "unpaid")):
            self.order(self.prod_low, quantity=100, amount="9000", category="Invalid", status=status, payment_status=payment)
        data = self.api({"period": "today"})["marketplace"]
        self.assertEqual(data["completed_orders"], 1)
        self.assertEqual(data["average_order_value"], 150)
        self.assertEqual(len(data["top_products"]), 1)
        self.assertEqual(data["top_products"][0]["units_sold"], 2)
        self.assertEqual([row["name"] for row in data["product_categories"]["categories"]], ["Valid"])

    def test_blank_categories_and_deleted_products_have_honest_fallbacks(self):
        self.order(category="")
        self.assertEqual(self.api()["marketplace"]["product_categories"]["categories"][0]["name"], self.prod_approved.category)
        self.prod_approved.delete()
        data = self.api()["marketplace"]
        self.assertEqual(data["product_categories"]["categories"][0]["name"], "Uncategorized")
        self.assertIsNone(data["top_products"][0]["id"])
        self.assertEqual(data["top_products"][0]["product_name"], "USTP Lanyard")
        self.assertEqual(data["top_products"][0]["category"], "Uncategorized")
        self.assertEqual(data["top_products"][0]["image_url"], "")

    def test_product_list_uses_real_image_and_category_with_historical_fallback(self):
        self.prod_approved.category = "Clothing"
        self.prod_approved.image_url = TEST_PRODUCT_IMAGE
        self.prod_approved.save(update_fields=["category", "image_url"])
        self.order(quantity=3, category="Original category")
        row = self.api({"period": "today"})["marketplace"]["top_products"][0]
        self.assertEqual(row["category"], "Clothing")
        self.assertEqual(row["units_sold"], 3)
        self.assertEqual(row["image_url"], reverse("product_image", args=[self.prod_approved.pk]))
        self.assertEqual(self.client.get(row["image_url"]).status_code, 200)
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
        self.assertContains(page, 'id="topSellingProductsChart"')
        self.assertContains(page, "Best-performing products based on units sold.")
        self.assertContains(page, '3 units sold.')
        self.prod_approved.delete()
        historical = self.api({"period": "today"})["marketplace"]["top_products"][0]
        self.assertEqual(historical["category"], "Original category")
        self.assertEqual(historical["image_url"], "")

    def test_single_item_orders_rank_without_association_rules(self):
        for quantity in (1, 2, 1):
            self.order(quantity=quantity, amount=str(quantity * 50), category="Clothing")
        self.order(self.prod_low, category="Sports", amount="25")
        with patch("modules.marketplace.services.analytics.calculate_market_basket") as association:
            data = self.api({"period": "today"})["marketplace"]
        association.assert_not_called()
        self.assertEqual([row["units_sold"] for row in data["top_products"]], [4, 1])
        self.assertEqual(data["sales_overview"]["metrics"][0]["value"], "225.00")
        self.assertEqual(data["completed_orders"], 4)
        self.assertEqual(data["product_categories"]["total"], 4)

    def test_zero_quantity_transactions_are_not_valid_sales(self):
        valid = self.order(quantity=1)
        invalid = self.order(quantity=1, amount="999")
        MarketplaceOrder.objects.filter(pk=invalid.pk).update(quantity=0)
        data = self.api({"period": "today"})["marketplace"]
        self.assertEqual(data["completed_orders"], 1)
        self.assertEqual(data["top_products"][0]["units_sold"], valid.quantity)
        self.assertEqual(data["top_products"][0]["sales"], "100.00")

    def test_period_controls_both_summaries_and_grouping_preserves_them(self):
        self.order(category="Current", day=self.today)
        self.order(self.prod_low, quantity=5, category="Earlier", day=self.today - timedelta(days=15))
        today = self.api({"period": "today"})["marketplace"]
        last30 = self.api({"period": "last_30_days"})["marketplace"]
        self.assertEqual(len(today["top_products"]), 1)
        self.assertEqual(len(last30["top_products"]), 2)
        self.assertEqual(today["product_categories"]["total"], 1)
        self.assertEqual(last30["product_categories"]["total"], 2)
        for period in ("today", "last_7_days", "last_30_days", "this_month", "this_year", "custom"):
            baseline = None
            for grouping in ("daily", "weekly", "monthly"):
                data = self.api({"period": period, "grouping": grouping, "start_date": "2026-09-01", "end_date": "2026-10-04"})["marketplace"]
                current = (data["top_products"], data["product_categories"], data["completed_orders"], data["average_order_value"])
                if baseline is not None:
                    self.assertEqual(current, baseline)
                baseline = current
                self.assertEqual(sum(data["sales_trend"]["orders"]), data["completed_orders"])

    def test_summaries_use_two_queries_without_per_product_lookups(self):
        valid = MarketplaceOrder.objects.filter(status="completed", payment_status="paid")
        with CaptureQueriesContext(connection) as empty:
            top_selling_products(valid)
            sales_by_product_category(valid)
        for index in range(30):
            self.order(quantity=2, category=f"Category {index}")
        with CaptureQueriesContext(connection) as populated:
            top_selling_products(valid)
            categories = sales_by_product_category(valid)
        self.assertEqual(len(empty), 2)
        self.assertEqual(len(populated), 2)
        self.assertEqual(len(categories["categories"]), 30)
        self.write_category_review("many")

    def test_empty_layout_keeps_chart_footprint_and_writes_review_artifacts(self):
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        for state in ("empty", "populated"):
            if state == "populated":
                for index, quantity in enumerate((25, 18, 12, 10, 8, 4)):
                    product = Product.objects.create(seller=self.seller, name=f"Test product {index + 1}", category="Clothing" if index < 3 else "Sports", price=100, image_url=TEST_PRODUCT_IMAGE if index == 0 else "")
                    self.order(product, quantity, str(quantity * 100), category=product.category)
            with patch("django.utils.timezone.localdate", return_value=self.today):
                page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
            self.assertContains(page, '<h3 id="salesOverviewTitle">Sales Summary</h3>')
            self.assertNotContains(page, 'Monitor marketplace sales for the selected period.')
            self.assertContains(page, "Monitor marketplace performance and activity.")
            self.assertContains(page, "Sales Trend")
            self.assertContains(page, "Top-Selling Products")
            self.assertNotContains(page, "Data is based on completed orders with confirmed payment (Cash on Pickup).")
            self.assertNotContains(page, '<footer class="sales-overview__footer">')
            self.assertNotContains(page, 'id="categorySalesCard"')
            self.assertContains(page, 'class="sales-overview__canvas" data-has-sales=')
            self.assertNotContains(page, '<div class="sales-overview__canvas" hidden>')
            if state == "empty":
                self.assertContains(page, 'data-has-sales="false" hidden')
                self.assertNotContains(page, '<canvas id="salesOverviewChart" hidden')
                self.assertContains(page, "No completed sales in this period.")
                self.assertContains(page, "No Sales Data Yet")
                self.assertContains(page, "No Top-Selling Products Yet")
                self.assertContains(page, "Unable to load sales analytics.")
                trend = self.api({"period": "today"})["marketplace"]["sales_trend"]
                self.assertTrue(trend["labels"])
                self.assertEqual(trend["sales"], [0])
                self.assertEqual(trend["orders"], [0])
                self.assertNotContains(page, "Sales by Product Categories")
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
                Path(directory, f"ranking-{state}.html").write_bytes(page.content)
                Path(directory, f"ranking-{state}.json").write_text(json.dumps(self.api({"period": "today"})), encoding="utf-8")
                Path(directory, "ranking-product-images.json").write_text(json.dumps({reverse("product_image", args=[product.pk]): product.image_url for product in Product.objects.exclude(image_url="")}), encoding="utf-8")
                weekly_params = {"period": "last_30_days", "grouping": "weekly"}
                with patch("django.utils.timezone.localdate", return_value=self.today):
                    weekly_page = self.client.get(reverse("admin_dashboard_page"), weekly_params)
                Path(directory, f"ranking-{state}-weekly.html").write_bytes(weekly_page.content)
                Path(directory, f"ranking-{state}-weekly.json").write_text(json.dumps(self.api(weekly_params)), encoding="utf-8")

    def test_zero_value_paid_order_does_not_claim_no_completed_orders(self):
        self.order(amount="0")
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
        self.assertNotContains(page, "No completed orders this period.")
        import re
        secondary = re.search(r'data-dashboard-secondary="marketplace_revenue"[^>]*>([^<]+)</small>', page.content.decode()).group(1)
        self.assertNotIn('No completed paid sales', secondary)
        self.assertEqual(self.api({"period": "today"})["marketplace"]["completed_orders"], 1)
