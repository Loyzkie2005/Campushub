from datetime import date, datetime, time, timedelta
from decimal import Decimal
import os
from pathlib import Path

from django.db.models.functions import Coalesce
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from api.models import MarketplaceOrder
from modules.marketplace.services.analytics import AnalyticsPeriod, _sales_time_series
from modules.reports.views import _revenue_orders


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SalesReportRevenueTests(TestCase):
    """Report/preview/exports recognize only completed, paid test orders."""

    def setUp(self):
        from accounts.models import Department, User
        from api.models import Product

        self.program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name": "Information Technology", "is_program": True})
        self.admin = User.objects.create_superuser(username="sales-report-admin", role="Super Admin", department=self.program)
        self.product = Product.objects.create(seller=self.admin, name="Revenue test product", price="10.00", stock=600, approval_status="approved")
        self.day = date(2026, 10, 15)
        self.params = {"report_type": "sales", "date_from": self.day.isoformat(), "date_to": self.day.isoformat()}
        self.client.force_login(self.admin)
        self.included = [self.order("GOODSALE0001", "106.50", quantity=3), self.order("GOODSALE0002", "213.50")]
        self.excluded = [
            self.order("EXCLUDED0001", "901.01", payment=MarketplaceOrder.PAYMENT_UNPAID),
            self.order("EXCLUDED0002", "902.02", status=MarketplaceOrder.STATUS_PENDING),
            self.order("EXCLUDED0003", "903.03", status=MarketplaceOrder.STATUS_PROCESSING),
            self.order("EXCLUDED0004", "904.04", status=MarketplaceOrder.STATUS_CANCELLED),
            self.order("EXCLUDED0005", "905.05", status=MarketplaceOrder.STATUS_READY_FOR_PICKUP),
        ]

    def order(self, code, amount, *, status=MarketplaceOrder.STATUS_COMPLETED, payment=MarketplaceOrder.PAYMENT_PAID, quantity=1, day=None, product=None):
        day = day or self.day
        timestamp = timezone.make_aware(datetime.combine(day, time(12)))
        order = MarketplaceOrder.objects.create(product=product or self.product, order_code=code,
            product_name="Revenue test product", quantity=quantity, unit_price=Decimal(amount) / quantity,
            total_price=amount, status=status, payment_status=payment,
            completed_at=timestamp if status == MarketplaceOrder.STATUS_COMPLETED else None,
            paid_at=timestamp if payment == MarketplaceOrder.PAYMENT_PAID else None)
        MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=timestamp)
        return order

    def report(self):
        from modules.reports.reporting import build_report
        return build_report("sales", self.day, self.day, user=self.admin)

    def test_status_matrix_totals_chart_and_dashboard_eligibility(self):
        from django.db.models import Sum

        report = self.report()
        expected = {order.order_code for order in self.included}
        actual = {row["Order ID"] for row in report["rows"]}
        for order in self.included + self.excluded:
            with self.subTest(status=order.status, payment=order.payment_status):
                self.assertEqual(order.order_code in actual, order in self.included)
        self.assertEqual(actual, expected)
        dashboard_orders = _revenue_orders(user=self.admin).filter(created_at__date=self.day)
        self.assertEqual(actual, set(dashboard_orders.values_list("order_code", flat=True)))
        report_total = sum(Decimal(row["Amount (PHP)"]) for row in report["rows"])
        self.assertEqual(report_total, Decimal("320.00"))
        self.assertEqual(report_total, dashboard_orders.aggregate(total=Sum("total_price"))["total"])
        self.assertEqual({row["label"]: row["value"] for row in report["summary"]}, {
            "Completed & Paid Orders": 2, "Products Sold": 4, "Revenue": "PHP 320.00", "Average Order Value": "PHP 160.00"})
        self.assertEqual(report["chart"]["values"], [320.0])

    def test_sales_recognition_date_filter_keeps_orders_report_on_creation_date(self):
        from modules.reports.reporting import build_report
        outside = self.order("OUTSIDEDATE1", "999.00", day=self.day - timedelta(days=1))
        MarketplaceOrder.objects.filter(pk=outside.pk).update(completed_at=timezone.make_aware(datetime.combine(self.day, time(12))))
        self.order("OUTSIDEDATE2", "999.00", day=self.day + timedelta(days=1))
        self.assertEqual(len(self.report()["rows"]), 3)
        orders = build_report("orders", self.day, self.day, user=self.admin)
        self.assertEqual(len(orders["rows"]), 7)
        self.assertTrue({order.order_code for order in self.excluded}.issubset({row["Order ID"] for row in orders["rows"]}))

    def test_preview_page_csv_and_pdf_share_eligible_values(self):
        import csv
        import json
        from io import StringIO
        from unittest.mock import patch
        from reportlab.platypus import Table
        from modules.reports.models import GeneratedReport

        preview = self.client.get(reverse("admin_report_preview"), self.params)
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json(), self.report())
        page = self.client.get(reverse("admin_generate_reports_page"), self.params)
        self.assertEqual(page.context["initial_report"], self.report())
        csv_response = self.client.get(reverse("admin_report_download"), {**self.params, "format": "csv"})
        self.assertEqual(csv_response.status_code, 200)
        self.assertTrue(csv_response["Content-Type"].startswith("text/csv"))
        csv_rows = list(csv.reader(StringIO(csv_response.content.decode())))[2:]
        self.assertEqual({row[0] for row in csv_rows}, {order.order_code for order in self.included})
        self.assertEqual(sum(Decimal(row[4]) for row in csv_rows), Decimal("320.00"))
        with patch("reportlab.platypus.Table", wraps=Table) as rendered_table:
            pdf_response = self.client.get(reverse("admin_report_download"), {**self.params, "format": "pdf"})
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF-"))
        pdf_rows = rendered_table.call_args.args[0][1:]
        self.assertEqual(pdf_rows, csv_rows)
        self.assertEqual(list(GeneratedReport.objects.values_list("row_count", flat=True)), [2, 2])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 600)
        directory = os.environ.get("SALES_REPORT_REVIEW_DIR")
        if directory:
            root = Path(directory); root.mkdir(parents=True, exist_ok=True)
            (root / "sales.csv").write_bytes(csv_response.content)
            (root / "sales.pdf").write_bytes(pdf_response.content)
            (root / "preview.json").write_text(json.dumps(preview.json()), encoding="utf-8")
            (root / "eligibility.json").write_text(json.dumps({"included": [order.order_code for order in self.included], "excluded": [order.order_code for order in self.excluded]}), encoding="utf-8")
            (root / "report.html").write_bytes(page.content)

    def test_excluded_orders_alone_produce_zero_revenue(self):
        MarketplaceOrder.objects.filter(pk__in=[order.pk for order in self.included]).delete()
        report = self.report()
        self.assertEqual(report["rows"], [])
        self.assertEqual(report["chart"]["values"], [])
        self.assertEqual({row["label"]: row["value"] for row in report["summary"]}, {
            "Completed & Paid Orders": 0, "Products Sold": 0, "Revenue": "PHP 0.00", "Average Order Value": "PHP 0.00"})

    def test_report_permission_gate_is_preserved(self):
        from accounts.models import User
        from accounts.role_permissions import sync_user_admin_permissions
        from modules.reports.models import GeneratedReport

        facilities_admin = User.objects.create_user(username="sales-report-denied", role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(facilities_admin)
        self.client.force_login(facilities_admin)
        for endpoint in ("admin_report_preview", "admin_report_download"):
            self.assertEqual(self.client.get(reverse(endpoint), self.params).status_code, 403)
        self.assertFalse(GeneratedReport.objects.exists())

    def test_marketplace_program_scope_is_preserved(self):
        from accounts.models import Department, User
        from accounts.role_permissions import sync_user_admin_permissions
        from api.models import Product

        other_program, _ = Department.objects.get_or_create(code="BFPT", defaults={"name": "Food Processing", "is_program": True})
        foreign_owner = User.objects.create_user(username="sales-report-foreign", department=other_program)
        foreign_product = Product.objects.create(seller=foreign_owner, name="Foreign scope product", price=10, stock=10)
        self.order("OTHERSCOPE01", "999.00", product=foreign_product)
        scoped_admin = User.objects.create_user(username="sales-report-scoped", role="Marketplace Admin", is_staff=True, department=self.program)
        sync_user_admin_permissions(scoped_admin)
        self.client.force_login(scoped_admin)
        response = self.client.get(reverse("admin_report_preview"), self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row["Order ID"] for row in response.json()["rows"]}, {order.order_code for order in self.included})


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SalesOverviewTests(fixtures.DedicatedDomainDashboardTests):
    def test_only_compact_marketplace_moves_date_controls_out_of_shared_sales_header(self):
        from django.template.loader import render_to_string
        for context in [{}, {'marketplace': {'top_selling_products': []}}, {'global_dashboard': True}]:
            html = render_to_string('dashboard/partials/sales_overview.html', context)
            self.assertIn('id="salesGroupingSelect"', html)
            self.assertEqual('id="salesPeriodSelect"' in html, not context.get('global_dashboard', False))
        compact = render_to_string('dashboard/partials/sales_overview.html', {'marketplace_compact': True})
        self.assertIn('id="salesGroupingSelect"', compact)
        self.assertNotIn('id="salesPeriodSelect"', compact)
        self.assertNotIn('id="salesCustomDates"', compact)

    def test_marketplace_comparison_opt_in_preserves_legacy_summary_and_shared_output(self):
        from django.template import Context, Engine
        from django.template.loader import render_to_string
        from modules.marketplace.services.analytics import valid_sales_queryset
        from modules.reports.views import _sales_overview_summary
        period=AnalyticsPeriod('30','Last 30 Days',timezone.localdate()-timedelta(days=29),timezone.localdate())
        legacy=_sales_overview_summary(valid_sales_queryset(self.super_admin),period,Decimal('0'),0)
        self.assertNotIn('comparison',legacy)
        self.assertTrue(all('comparison' not in row for row in legacy['metrics']))
        self.assertEqual(legacy['metrics'][2]['value'],'0.00')
        directory=os.environ.get('MARKETPLACE_ANALYTICS_REVIEW_DIR')
        if directory:
            before=Path(directory)/'before/backend/templates/dashboard/partials/sales_overview.html'
            for context in [{'sales_overview':legacy}, {'executive_mode':True,'sales_overview':legacy},
                            {'marketplace':{'top_selling_products':[]},'sales_overview':legacy}]:
                current=render_to_string('dashboard/partials/sales_overview.html',context)
                old=Engine.get_default().from_string(before.read_text(encoding='utf-8')).render(Context(context))
                self.assertEqual(' '.join(current.split()),' '.join(old.split()))
        page=self.dashboard(user=self.super_admin)
        self.assertNotContains(page,'marketplace-metric-comparison')
        self.assertNotContains(page,'marketplace-comparison-period')

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
        self.assertContains(response, 'data-executive-analytics="marketplace"')
        self.assertContains(response, 'View Analytics')

    def test_empty_data_has_zero_buckets_and_safe_average(self):
        MarketplaceOrder.objects.all().delete()
        response = self.dashboard(snapshot="empty")
        self.assertEqual(response.context["revenue_chart"]["sales"], [0] * 30)
        self.assertEqual(response.context["revenue_chart"]["orders"], [0] * 30)
        self.assertEqual(self.metrics(response)["average"]["value"], "0.00")
        self.assertContains(response, "No completed sales in this period.")

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
                    self.assertContains(response, 'id="dashboardGlobalControls"')
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
        self.assertTemplateUsed(response, "marketplace/partials/dashboard_top_products.html")
        self.assertTemplateUsed(response, "dashboard/partials/sales_overview.html")
        self.assertEqual(self.metrics(response)["sales"]["value"], "300.00")
        self.assertEqual(self.metrics(response)["orders"]["value"], "1")
        self.assertEqual(self.metrics(response)["average"]["value"], "300.00")
        self.assertContains(response, 'id="salesOverviewChart"', count=1)
        self.assertContains(response, 'id="marketplaceTopProductsTitle"', count=1)
        self.assertNotContains(response, 'id="productCategoriesTitle"')
        self.assertNotContains(response, 'id="orderStatusChart"')
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
