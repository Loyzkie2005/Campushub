from datetime import date, datetime, time, timedelta
from decimal import Decimal
import os
from pathlib import Path

from django.db.models.functions import Coalesce
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from api.models import MarketplaceOrder
from modules.marketplace.services.analytics import AnalyticsPeriod, _sales_time_series
from modules.reports.views import _revenue_orders


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SalesOverviewTests(fixtures.DedicatedDomainDashboardTests):
    def dashboard(self, params=None, snapshot=None, user=None):
        self.client.force_login(user or self.super_admin)
        query = {"facility_days": "14"} if snapshot else {}
        query.update(params or {})
        response = self.client.get(reverse("admin_dashboard_page"), query)
        self.assertEqual(response.status_code, 200)
        directory = os.environ.get("SALES_OVERVIEW_REVIEW_DIR")
        if directory and snapshot:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / f"{snapshot}.html").write_bytes(response.content)
        return response

    def new_order(self, day, amount="100.00", **kwargs):
        return MarketplaceOrder.objects.create(
            product=self.prod_approved, buyer_name="Test buyer", product_name="Test product",
            quantity=1, unit_price=Decimal(amount), total_price=Decimal(amount),
            status=kwargs.pop("status", MarketplaceOrder.STATUS_COMPLETED),
            payment_status=kwargs.pop("payment_status", MarketplaceOrder.PAYMENT_PAID),
            completed_at=timezone.make_aware(datetime.combine(day, time(12))), **kwargs,
        )

    def metrics(self, response):
        return {item["key"]: item for item in response.context["sales_overview"]["metrics"]}

    def test_one_paid_order_and_new_component(self):
        response = self.dashboard(snapshot="single")
        metrics = self.metrics(response)
        self.assertEqual(metrics["sales"]["value"], "300.00")
        self.assertEqual(metrics["orders"]["value"], "1")
        self.assertEqual(metrics["average"]["value"], "300.00")
        self.assertEqual(metrics["sales"]["change"], "No previous sales")
        self.assertContains(response, 'id="salesOverviewChart"')
        self.assertNotContains(response, 'id="revenueOverviewChart"')
        self.assertContains(response, "admin_sales_overview.js")
        self.assertNotContains(response, "admin_super_dashboard.js")
        self.assertContains(response, "View Detailed Analytics")

    def test_empty_data_has_zero_buckets_and_safe_average(self):
        MarketplaceOrder.objects.all().delete()
        response = self.dashboard(snapshot="empty")
        self.assertEqual(response.context["revenue_chart"]["sales"], [0] * 30)
        self.assertEqual(response.context["revenue_chart"]["orders"], [0] * 30)
        self.assertEqual(self.metrics(response)["average"]["value"], "0.00")
        self.assertContains(response, "No completed sales in the selected period.")

    def test_period_and_grouping_are_independent_and_preserve_filters(self):
        self.new_order(timezone.localdate() - timedelta(days=8), "100.00")
        for grouping in ("daily", "weekly", "monthly"):
            for days in (7, 14, 30):
                with self.subTest(grouping=grouping, days=days):
                    response = self.dashboard({"grouping": grouping, "sales_days": days, "facility_days": "14"})
                    self.assertEqual(response.context["sales_overview"]["days"], days)
                    chart = response.context["revenue_chart"]
                    self.assertEqual(sum(chart["sales"]), 300 if days == 7 else 400)
                    self.assertEqual(sum(chart["orders"]), 1 if days == 7 else 2)
                    self.assertContains(response, 'name="facility_days" value="14"')
                    if grouping == "daily":
                        self.assertEqual(len(chart["labels"]), days)
        response = self.dashboard({"grouping": "invalid", "sales_days": "invalid"})
        self.assertEqual(response.context["sales_days"], 30)
        self.assertEqual(response.context["sales_grouping"], "daily")

    def test_comparison_same_day_multiple_orders_and_exclusions(self):
        today = timezone.localdate()
        self.new_order(today, "100.00")
        self.new_order(today - timedelta(days=30), "200.00")
        self.new_order(today - timedelta(days=60), "9900.00")
        self.new_order(today, "9900.00", status=MarketplaceOrder.STATUS_CANCELLED)
        self.new_order(today, "9900.00", payment_status=MarketplaceOrder.PAYMENT_UNPAID)
        response = self.dashboard(snapshot="populated")
        metrics = self.metrics(response)
        self.assertEqual(metrics["sales"]["value"], "400.00")
        self.assertEqual(metrics["orders"]["value"], "2")
        self.assertEqual(metrics["average"]["value"], "200.00")
        self.assertEqual(metrics["sales"]["change"], "+100.0%")
        self.assertEqual(metrics["orders"]["change"], "+100.0%")
        self.assertEqual(metrics["average"]["change"], "0.0%")
        self.assertEqual(response.context["revenue_chart"]["orders"][-1], 2)

    def test_missing_days_weeks_months_and_one_day(self):
        MarketplaceOrder.objects.all().delete()
        self.new_order(date(2026, 8, 30), "150.00")
        self.new_order(date(2026, 9, 1), "10.00")
        orders = _revenue_orders().annotate(analytics_at=Coalesce("completed_at", "paid_at", "created_at"))
        period = AnalyticsPeriod("custom", "Test", date(2026, 8, 30), date(2026, 9, 1))
        chart = _sales_time_series(orders, period, "daily")
        self.assertEqual(chart["sales"], [150, 0, 10])
        self.assertEqual(chart["orders"], [1, 0, 1])
        one_day = AnalyticsPeriod("custom", "Test", date(2026, 8, 30), date(2026, 8, 30))
        self.assertEqual(_sales_time_series(orders, one_day, "daily")["sales"], [150])
        months = AnalyticsPeriod("custom", "Test", date(2026, 7, 1), date(2026, 10, 31))
        self.assertEqual(_sales_time_series(orders, months, "monthly")["orders"], [0, 1, 1, 0])
        weeks = AnalyticsPeriod("custom", "Test", date(2026, 8, 17), date(2026, 9, 13))
        self.assertEqual(_sales_time_series(orders, weeks, "weekly")["orders"], [0, 1, 1, 0])

    def test_previous_sales_but_no_current_orders(self):
        MarketplaceOrder.objects.all().delete()
        self.new_order(timezone.localdate() - timedelta(days=30))
        metrics = self.metrics(self.dashboard())
        self.assertEqual(metrics["sales"]["change"], "-100.0%")
        self.assertEqual(metrics["average"]["value"], "0.00")

    def test_ajax_summary_matches_chart(self):
        self.client.force_login(self.super_admin)
        payload = self.client.get(reverse("admin_dashboard_page"), {"sales_days": 7, "grouping": "weekly"},
                                  HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
        self.assertEqual(payload["sales_overview"]["days"], 7)
        self.assertEqual(sum(payload["sales_chart"]["orders"]), payload["period_completed_orders"])

    def test_marketplace_overview_uses_same_component_and_real_metrics(self):
        response = self.dashboard(user=self.marketplace_admin, snapshot="marketplace-populated")
        self.assertTemplateUsed(response, "dashboard/partials/marketplace_overview_row.html")
        self.assertTemplateUsed(response, "dashboard/partials/sales_overview.html")
        self.assertEqual(self.metrics(response)["sales"]["value"], "300.00")
        self.assertEqual(self.metrics(response)["orders"]["value"], "1")
        self.assertEqual(self.metrics(response)["average"]["value"], "300.00")
        self.assertContains(response, 'id="salesOverviewChart"', count=1)
        self.assertContains(response, 'id="topProductsTitle"', count=1)
        self.assertContains(response, 'id="productCategoriesTitle"', count=1)
        self.assertContains(response, 'id="orderStatusChart"', count=1)
        self.assertNotContains(response, 'id="salesTrendChart"')
        self.assertEqual(response.context["overview_categories"]["total"], 2)
        statuses = response.context["marketplace"]["order_status"]
        self.assertIsInstance(statuses, list)
        self.assertEqual(sum(row["count"] for row in statuses), 2)
        self.assertEqual(next(row for row in statuses if row["key"] == "completed")["count"], 1)

    def test_marketplace_empty_and_grouping_preserve_selected_range(self):
        MarketplaceOrder.objects.all().delete()
        response = self.dashboard(user=self.marketplace_admin, snapshot="marketplace-empty")
        self.assertEqual(self.metrics(response)["average"]["value"], "0.00")
        for grouping in ("daily", "weekly", "monthly"):
            for days in (7, 14, 30):
                self.client.force_login(self.marketplace_admin)
                payload = self.client.get(reverse("admin_dashboard_page"), {"sales_days": days, "grouping": grouping},
                                          HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
                self.assertEqual(payload["sales_overview"]["days"], days)
                self.assertEqual(sum(payload["sales_chart"]["sales"]), 0)
                self.assertEqual(sum(payload["sales_chart"]["orders"]), 0)
                if grouping == "daily":
                    self.assertEqual(len(payload["sales_chart"]["labels"]), days)
        self.new_order(timezone.localdate(), "100.00")
        self.new_order(timezone.localdate() - timedelta(days=8), "200.00")
        for grouping in ("daily", "weekly", "monthly"):
            for days, expected in ((7, 100), (14, 300)):
                payload = self.client.get(reverse("admin_dashboard_page"), {"sales_days": days, "grouping": grouping},
                                          HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
                self.assertEqual(sum(payload["sales_chart"]["sales"]), expected)
                self.assertEqual(payload["sales_overview"]["days"], days)

    def test_marketplace_keeps_department_scope_for_all_three_panels(self):
        from accounts.models import Department, User
        from api.models import Product

        own = Department.objects.create(name="Own Department", code="OWN")
        other = Department.objects.create(name="Other Department", code="OTHER")
        for user in (self.marketplace_admin, self.seller):
            user.department = own
            user.save(update_fields=["department"])
        outsider = User.objects.create_user(username="outside-seller", role="Seller", department=other)
        product = Product.objects.create(seller=outsider, name="Outside product", category="Outside category", price=999, stock=1)
        MarketplaceOrder.objects.create(product=product, product_name=product.name, quantity=1, unit_price=999,
                                        total_price=999, status=MarketplaceOrder.STATUS_COMPLETED,
                                        payment_status=MarketplaceOrder.PAYMENT_PAID)
        response = self.dashboard(user=self.marketplace_admin)
        self.assertEqual(self.metrics(response)["sales"]["value"], "300.00")
        self.assertEqual(response.context["overview_categories"]["total"], 2)
        self.assertEqual(len(response.context["overview_top_products"]), 1)
        self.assertNotContains(response, "Outside product")
        self.assertNotContains(response, "Outside category")

    def test_categories_include_uncategorized_and_other_without_archived(self):
        from api.models import Product
        from modules.reports.views import _dashboard_product_categories

        for index in range(7):
            Product.objects.create(seller=self.seller, name=f"Product {index}", category=f"Category {index}", price=10, stock=1)
        Product.objects.create(seller=self.seller, name="Uncategorized", category="", price=10, stock=1)
        Product.objects.create(seller=self.seller, name="Archived", category="Archived", price=10, stock=1, is_archived=True)
        summary = _dashboard_product_categories(Product.objects.filter(is_archived=False))
        self.assertEqual(summary["total"], 10)
        self.assertEqual(sum(row["count"] for row in summary["categories"]), 10)
        self.assertEqual(summary["categories"][-1]["name"], "Other categories")
