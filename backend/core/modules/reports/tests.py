from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Permission

from accounts.models import User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import MarketplaceOrder, Product, SellerRequest
from modules.marketplace.services.analytics import (
    build_marketplace_analytics,
    calculate_market_basket,
)


class MarketplaceAnalyticsTests(TestCase):
    password = "CampusHub1!"
    today = date(2026, 9, 4)

    def setUp(self):
        self.marketplace_admin = User.objects.create_user(
            username="analytics-marketplace-admin",
            password=self.password,
            role="Marketplace Admin",
            is_staff=True,
        )
        self.facilities_admin = User.objects.create_user(
            username="analytics-facilities-admin",
            password=self.password,
            role="Facilities Admin",
            is_staff=True,
        )
        sync_user_admin_permissions(self.marketplace_admin)
        sync_user_admin_permissions(self.facilities_admin)

        self.seller = User.objects.create_user(
            username="analytics-seller",
            password=self.password,
            first_name="Campus",
            last_name="Seller",
            role="Seller",
        )
        SellerRequest.objects.create(
            user=self.seller,
            student_id="SELLER-001",
            full_name="Campus Seller",
            product_type="Campus supplies",
            status=SellerRequest.STATUS_APPROVED,
        )
        self.product = Product.objects.create(
            seller=self.seller,
            name="USTP Notebook",
            category="School Supplies",
            price=Decimal("50.00"),
            stock=20,
            approval_status=Product.STATUS_APPROVED,
        )
        self.variant_product = Product.objects.create(
            seller=self.seller,
            name="Campus Shirt",
            category="Merchandise",
            price=Decimal("200.00"),
            stock=0,
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Size",
                    "options": [
                        {"name": "Small", "stock": 2},
                        {"name": "Large", "stock": 3},
                    ],
                }
            ],
            approval_status=Product.STATUS_APPROVED,
        )
        self.out_of_stock = Product.objects.create(
            seller=self.seller,
            name="Sold Out Lanyard",
            category="Merchandise",
            price=Decimal("80.00"),
            stock=0,
            approval_status=Product.STATUS_APPROVED,
        )

    def _timestamp(self, day, hour=12):
        return timezone.make_aware(datetime.combine(day, time(hour=hour)))

    def _order(
        self,
        *,
        code,
        day,
        product=None,
        buyer_id=101,
        buyer_email="buyer@ustp.edu.ph",
        quantity=1,
        status=MarketplaceOrder.STATUS_COMPLETED,
        payment=MarketplaceOrder.PAYMENT_PAID,
    ):
        product = product or self.product
        order = MarketplaceOrder.objects.create(
            product=product,
            order_code=code,
            buyer_user_id=buyer_id,
            buyer_name=f"Buyer {buyer_id}",
            buyer_email=buyer_email,
            product_name=product.name,
            category=product.category,
            seller_name="Campus Seller",
            quantity=quantity,
            unit_price=product.price,
            total_price=product.price * quantity,
            status=status,
            payment_status=payment,
            paid_at=self._timestamp(day),
            completed_at=self._timestamp(day),
        )
        MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=self._timestamp(day))
        return order

    def test_empty_dataset_has_complete_zero_filled_daily_series(self):
        analytics = build_marketplace_analytics(
            {"period": "custom", "date_from": "2026-09-01", "date_to": "2026-09-03"},
            today=self.today,
        )

        self.assertEqual(analytics["kpis"]["sales"], "0.00")
        self.assertEqual(analytics["kpis"]["completed_orders"], 0)
        self.assertEqual(analytics["sales_chart"]["labels"], ["Sep 01", "Sep 02", "Sep 03"])
        self.assertEqual(analytics["sales_chart"]["sales"], [0.0, 0.0, 0.0])
        self.assertEqual(analytics["sales_chart"]["orders"], [0, 0, 0])
        self.assertEqual(analytics["kpis"]["average_order_value"], "0.00")
        self.assertFalse(analytics["forecast"]["sufficient"])
        self.assertFalse(analytics["market_basket"]["sufficient"])

    def test_only_completed_and_paid_orders_count_as_sales(self):
        day = self.today - timedelta(days=1)
        self._order(code="2026AN000001", day=day, quantity=2)
        self._order(code="2026AN000002", day=day, status=MarketplaceOrder.STATUS_CANCELLED)
        self._order(code="2026AN000003", day=day, payment=MarketplaceOrder.PAYMENT_UNPAID)

        analytics = build_marketplace_analytics({"period": "7"}, today=self.today)

        self.assertEqual(analytics["kpis"]["sales"], "100.00")
        self.assertEqual(analytics["kpis"]["completed_orders"], 1)
        self.assertEqual(analytics["kpis"]["average_order_value"], "100.00")
        self.assertEqual(sum(analytics["sales_chart"]["orders"]), 1)
        self.assertEqual(analytics["kpis"]["active_buyers"], 1)
        self.assertEqual(analytics["top_products"][0]["units"], 2)

    def test_multiple_buyers_and_repeat_buyer_are_calculated_from_orders(self):
        day = self.today - timedelta(days=1)
        self._order(code="2026BY000001", day=day, buyer_id=201)
        self._order(code="2026BY000002", day=day, buyer_id=201)
        self._order(code="2026BY000003", day=day, buyer_id=202, buyer_email="two@ustp.edu.ph")

        buyers = build_marketplace_analytics({"period": "7"}, today=self.today)["buyer_activity"]

        self.assertEqual(buyers["total"], 2)
        self.assertEqual(buyers["repeat"], 1)
        self.assertEqual(buyers["average_orders"], "1.50")

    def test_inventory_uses_variant_stock_and_handles_zero_sales(self):
        analytics = build_marketplace_analytics({"period": "7"}, today=self.today)
        rows = {row["product"]: row for row in analytics["inventory"]["all_rows"]}

        self.assertEqual(rows["Campus Shirt"]["stock"], 5)
        self.assertEqual(rows["Campus Shirt"]["state"], "Low Stock")
        self.assertEqual(rows["Campus Shirt"]["average_daily_sales"], "No recent sales")
        self.assertEqual(rows["Campus Shirt"]["days_left"], "Not available")
        self.assertEqual(rows["Sold Out Lanyard"]["state"], "Out of Stock")

    def test_daily_weekly_and_monthly_grouping_include_missing_periods(self):
        self._order(code="2026GR000001", day=date(2026, 8, 30))
        self._order(code="2026GR000002", day=date(2026, 9, 1))
        base = {"period": "custom", "date_from": "2026-08-30", "date_to": "2026-09-01"}

        daily = build_marketplace_analytics({**base, "grouping": "daily"}, today=self.today)
        weekly = build_marketplace_analytics({**base, "grouping": "weekly"}, today=self.today)
        monthly = build_marketplace_analytics({**base, "grouping": "monthly"}, today=self.today)

        self.assertEqual(daily["sales_chart"]["orders"], [1, 0, 1])
        self.assertEqual(len(weekly["sales_chart"]["labels"]), 2)
        self.assertEqual(weekly["sales_chart"]["orders"], [1, 1])
        self.assertEqual(monthly["sales_chart"]["labels"], ["Aug 2026", "Sep 2026"])

    def test_monthly_grouping_defaults_to_august_to_december_five_months(self):
        analytics = build_marketplace_analytics({"grouping": "monthly"}, today=self.today)
        expected_labels = ["Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026", "Dec 2026"]
        self.assertEqual(analytics["sales_chart"]["labels"], expected_labels)
        self.assertEqual(len(analytics["sales_chart"]["labels"]), 5)

    def test_sales_chart_counts_multiple_completed_paid_orders_in_one_bucket(self):
        day = self.today - timedelta(days=1)
        self._order(code="2026CH000001", day=day, quantity=1)
        self._order(code="2026CH000002", day=day, quantity=2, buyer_id=202)

        chart = build_marketplace_analytics({"period": "7"}, today=self.today)["sales_chart"]

        self.assertEqual(chart["orders"][-2], 2)
        self.assertEqual(chart["sales"][-2], 150.0)

    def test_sales_chart_frontend_uses_mixed_datasets_and_dual_axes(self):
        script_path = (
            Path(settings.BASE_DIR).parent
            / "static"
            / "components"
            / "js"
            / "admin_marketplace_analytics.js"
        )
        script = script_path.read_text(encoding="utf-8")

        self.assertIn("label: 'Sales (₱)'", script)
        self.assertIn("label: 'Orders'", script)
        self.assertIn("type: 'line'", script)
        self.assertIn("type: 'bar'", script)
        self.assertIn("yAxisID: 'ySales'", script)
        self.assertIn("yAxisID: 'yOrders'", script)
        self.assertIn("yTitle: 'Sales Amount (₱)'", script)
        self.assertIn("text: 'Date / Time Period'", script)
        self.assertIn("options.scales.x.title.display = false", script)
        self.assertGreaterEqual(script.count("title: { display: false }"), 2)
        self.assertNotIn("text: 'Number of Orders'", script)
        self.assertIn("stepSize: 10", script)
        self.assertIn("suggestedMax: 50", script)
        self.assertIn("suggestedMax: 10000", script)
        self.assertIn("stepSize = 2000", script)
        self.assertIn("options.plugins.legend.position = 'top'", script)
        self.assertIn("options.plugins.legend.align = 'center'", script)
        self.assertIn("usePointStyle: true", script)
        self.assertIn("pointStyle: 'rect'", script)
        self.assertIn("padding: 24", script)

    def test_one_day_range_produces_one_bucket_and_peak_period(self):
        self._order(code="2026PK000001", day=self.today, quantity=2)

        analytics = build_marketplace_analytics(
            {"period": "custom", "date_from": self.today.isoformat(), "date_to": self.today.isoformat()},
            today=self.today,
        )

        self.assertEqual(len(analytics["sales_chart"]["labels"]), 1)
        self.assertEqual(analytics["sales_chart"]["orders"], [1])
        self.assertTrue(analytics["peak_sales"]["sufficient"])
        self.assertEqual(analytics["peak_sales"]["time"], "12:00 PM - 3:00 PM")

    def test_multiple_approved_sellers_have_separate_performance(self):
        second_seller = User.objects.create_user(
            username="analytics-seller-two",
            password=self.password,
            first_name="Second",
            last_name="Seller",
            role="Seller",
        )
        SellerRequest.objects.create(
            user=second_seller,
            student_id="SELLER-002",
            full_name="Second Seller",
            product_type="Food",
            status=SellerRequest.STATUS_APPROVED,
        )
        second_product = Product.objects.create(
            seller=second_seller,
            name="Banana Cue",
            category="Food",
            price=Decimal("25.00"),
            stock=3,
            approval_status=Product.STATUS_APPROVED,
        )
        self._order(code="2026SL000001", day=self.today, product=self.product, quantity=2)
        self._order(code="2026SL000002", day=self.today, product=second_product, buyer_id=202, quantity=3)

        sellers = build_marketplace_analytics({"period": "7"}, today=self.today)["seller_performance"]

        self.assertEqual(sellers["active_count"], 2)
        self.assertEqual({row["seller"] for row in sellers["rows"]}, {"Campus Seller", "Second Seller"})
        second_row = next(row for row in sellers["rows"] if row["seller"] == "Second Seller")
        self.assertEqual(second_row["units"], 3)
        self.assertEqual(second_row["low_stock"], 1)

    def test_forecast_requires_history_then_uses_moving_average(self):
        start = self.today - timedelta(days=13)
        insufficient = build_marketplace_analytics(
            {"period": "custom", "date_from": start.isoformat(), "date_to": self.today.isoformat()},
            today=self.today,
        )
        self.assertFalse(insufficient["forecast"]["sufficient"])

        for index, offset in enumerate((0, 3, 6, 9, 12)):
            self._order(code=f"2026FC{index:06d}", day=start + timedelta(days=offset), quantity=2)
        sufficient = build_marketplace_analytics(
            {
                "period": "custom",
                "date_from": start.isoformat(),
                "date_to": self.today.isoformat(),
                "forecast_product": str(self.product.id),
                "forecast_horizon": "7",
            },
            today=self.today,
        )["forecast"]

        self.assertTrue(sufficient["sufficient"])
        self.assertEqual(sufficient["method"], "7-day moving average")
        self.assertGreater(sufficient["forecast_total"], 0)
        self.assertEqual(sufficient["suggested_preparation"], max(sufficient["forecast_total"] - sufficient["current_stock"], 0))

    def test_slow_moving_products_use_documented_minimum_history_rule(self):
        start = self.today - timedelta(days=29)
        for index in range(5):
            self._order(
                code=f"2026SM{index:06d}",
                day=start + timedelta(days=index * 5),
                quantity=1,
            )

        result = build_marketplace_analytics(
            {"period": "custom", "date_from": start.isoformat(), "date_to": self.today.isoformat()},
            today=self.today,
        )["slow_moving"]

        self.assertTrue(result["sufficient"])
        self.assertIn("Campus Shirt", {row["product"] for row in result["rows"]})
        self.assertNotIn("USTP Notebook", {row["product"] for row in result["rows"]})

    def test_market_basket_support_confidence_and_lift(self):
        result = calculate_market_basket(
            [
                [(1, "Notebook"), (2, "Pen")],
                [(1, "Notebook"), (2, "Pen")],
                [(1, "Notebook"), (3, "Envelope")],
            ]
        )

        self.assertTrue(result["sufficient"])
        notebook_to_pen = next(row for row in result["rows"] if row["product_a"] == "Notebook" and row["product_b"] == "Pen")
        self.assertEqual(notebook_to_pen["support"], 66.7)
        self.assertEqual(notebook_to_pen["confidence"], 66.7)
        self.assertEqual(notebook_to_pen["lift"], 1.0)

    def test_marketplace_admin_allowed_and_facilities_admin_blocked(self):
        self.client.force_login(self.marketplace_admin)
        allowed = self.client.get(reverse("admin_marketplace_analytics_page"))
        self.assertEqual(allowed.status_code, 200)
        self.assertContains(allowed, "Decision Support")
        self.assertContains(allowed, "admin_marketplace_analytics.js")
        self.assertContains(allowed, "Completed and paid Cash on Pickup orders")
        self.assertNotContains(allowed, "No completed sales in the selected period.")
        self.assertNotContains(allowed, "Analyze marketplace sales, buyer activity")
        self.assertNotContains(allowed, 'class="analytics-summary-row"')

        self.client.force_login(self.facilities_admin)
        blocked = self.client.get(reverse("admin_marketplace_analytics_page"))
        self.assertEqual(blocked.status_code, 403)

    def test_marketplace_admin_cannot_open_user_monitoring_even_if_permission_is_added(self):
        permission = Permission.objects.get(
            codename="can_view_user_monitoring",
            content_type__app_label="accounts",
        )
        self.marketplace_admin.user_permissions.add(permission)
        self.client.force_login(self.marketplace_admin)

        response = self.client.get(reverse("admin_user_monitoring_page"))

        self.assertEqual(response.status_code, 403)
