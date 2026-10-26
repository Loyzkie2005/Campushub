"""Scoped real-record dashboard boundaries, including conflicting audit metadata."""
import json
import os
import re
from datetime import datetime, time, timedelta
from pathlib import Path

from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from accounts.models import AccountActivity, Department, ProgramMajor, User
from api.models import MarketplaceOrder, Product, SellerRequest


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MarketplaceAdminDashboardTests(fixtures.DedicatedDomainDashboardTests):
    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        self.program, _ = Department.objects.get_or_create(code="BTLED", defaults={"name": "BTLED", "is_program": True})
        self.major, _ = ProgramMajor.objects.get_or_create(program=self.program, code="ICT", defaults={"name": "Information and Communication Technology"})
        self.other_major, _ = ProgramMajor.objects.get_or_create(program=self.program, code="HE", defaults={"name": "Home Economics"})
        for user in (self.marketplace_admin, self.seller):
            user.department = self.program
            user.major = self.major
            user.save(update_fields=["department", "major"])
        self.seller.role = "User"
        self.seller.save(update_fields=["role"])
        self.outside = User.objects.create_user(username="other-major-seller", role="User", department=self.program, major=self.other_major)
        self.outside_product = Product.objects.create(seller=self.outside, name="Outside Scope Product", category="Outside Category", price=900, stock=1)
        self.outside_order = MarketplaceOrder.objects.create(product=self.outside_product, product_name=self.outside_product.name,
            order_code="OUTSIDE-ORDER", quantity=1, total_price=900, unit_price=900, status="completed", payment_status="paid")
        SellerRequest.objects.create(user=self.seller, student_id=self.seller.username, full_name="Scoped Seller", product_type="Supplies", status="approved")
        SellerRequest.objects.create(user=self.outside, student_id=self.outside.username, full_name="Outside Seller", product_type="Supplies", status="pending")
        self.client.force_login(self.marketplace_admin)

    def dashboard(self, params=None):
        response = self.client.get(reverse("admin_dashboard_page"), params or {})
        self.assertEqual(response.status_code, 200)
        return response

    def event(self, code="PRODUCT_UPDATED", module="Marketplace", **metadata):
        return AccountActivity.objects.create(account_source="admin", account_id=self.seller.pk,
            account_ref=f"admin:{self.seller.pk}", activity_type=code, module=module,
            activity=code + " recorded", result="success", metadata={"actor_admin_id": self.marketplace_admin.pk, **metadata})

    def test_header_uses_authenticated_name_one_external_filter_and_compact_revenue(self):
        self.marketplace_admin.first_name = 'Lester <Admin>'
        self.marketplace_admin.last_name = 'Bulay'
        self.marketplace_admin.save(update_fields=['first_name', 'last_name'])
        page = self.dashboard({'period': '7', 'grouping': 'weekly', 'retained': 'yes'})
        html = page.content.decode()
        header = re.search(r'<header class="marketplace-dashboard-toolbar".*?</header>', html, re.S).group()
        self.assertIn('Welcome back, Lester &lt;Admin&gt;!', header)
        self.assertNotIn('Bulay', header)
        self.assertIn("Here's what's happening in your marketplace today.", header)
        self.assertContains(page, 'id="salesPeriodSelect"', count=1)
        self.assertContains(page, 'id="salesCustomDates"', count=1)
        for control in ['salesPeriodSelect', 'salesDateFrom', 'salesDateTo', 'salesApplyCustom']:
            tag = re.search(rf'<[^>]*id="{control}"[^>]*>', header).group()
            self.assertIn('form="salesOverviewFilters"', tag)
        form = re.search(r'<form[^>]*id="salesOverviewFilters".*?</form>', html, re.S).group()
        self.assertIn('id="salesGroupingSelect"', form)
        self.assertNotIn('id="salesPeriodSelect"', form)
        self.assertIn('name="retained" value="yes"', form)
        self.assertIn('<option value="weekly" selected>', form)
        revenue = re.search(r'<article class="dashboard-stat-card h-100">(?:(?!</article>).)*Marketplace Revenue.*?</article>', html, re.S).group()
        self.assertIn('vs. previous period', revenue)
        self.assertNotIn('Recognized in period', revenue)
        self.assertNotIn('marketplace-kpi-note', revenue)
        self.assertIn('Recognized in selected period', html)
        self.assertIn('Previous period:', html)
        self.assertNotIn('admin_dashboard_filter.js', html)
        self.assertNotIn('id="dashboardGlobalControls"', html)
        self.marketplace_admin.first_name = self.marketplace_admin.last_name = ''
        self.marketplace_admin.save(update_fields=['first_name', 'last_name'])
        self.assertContains(self.dashboard(), f'Welcome back, {self.marketplace_admin.username}!')

    def test_header_timestamp_is_explicitly_philippine_local_response_time(self):
        from datetime import timezone as datetime_timezone
        from unittest.mock import patch
        stamp = datetime(2026, 10, 25, 18, 5, tzinfo=datetime_timezone.utc)
        with timezone.override(datetime_timezone.utc), patch('modules.reports.views.timezone.now', return_value=stamp):
            page = self.dashboard()
        self.assertContains(page, 'datetime="2026-10-26T02:05:00+08:00"')
        self.assertContains(page, 'Last Updated: Oct 26, 2026 2:05 AM PHT')
        self.assertContains(page, 'not a live synchronization timestamp')

    def test_header_presets_custom_grouping_and_snapshot_counts_stay_independent(self):
        initial = self.dashboard().context['marketplace']
        today = initial['today']
        cases = [{'period': key} for key in ['today', '7', '14', '30', '90', 'month', 'year']]
        cases += [{'period': 'custom', 'date_from': (today-timedelta(days=8)).isoformat(), 'date_to': today.isoformat()}]
        for params in cases:
            for grouping in ['daily', 'weekly', 'monthly']:
                with self.subTest(params=params, grouping=grouping):
                    page = self.dashboard({**params, 'grouping': grouping})
                    data = page.context['marketplace']
                    self.assertEqual((data['total_products'], data['pending_listings'], data['low_stock_products']),
                                     (initial['total_products'], initial['pending_listings'], initial['low_stock_products']))
                    self.assertEqual(data['sales_grouping'], grouping)
                    self.assertEqual(data['sales_period_key'], params['period'])
                    self.assertEqual(sum(data['sales_chart']['sales']), float(data['total_sales'].replace(',', '')))
                    html = page.content.decode()
                    header = re.search(r'<header class="marketplace-dashboard-toolbar".*?</header>', html, re.S).group()
                    self.assertIn(f'<option value="{params["period"]}" selected>', header)
                    self.assertIn(data['sales_period'].start.strftime('%b') + ' ' + str(data['sales_period'].start.day), header)
                    self.assertEqual(data['sales_overview']['comparison']['days'], data['sales_period'].days)

    def test_major_scope_covers_all_sections_and_ajax(self):
        response = self.dashboard()
        data = response.context["marketplace"]
        self.assertEqual((data["total_products"], data["total_orders"], data["total_sales"]), (2, 2, "300.00"))
        self.assertEqual(data["seller_overview"], {"approved": 1, "pending": 0, "suspended": 0})
        self.assertEqual(data["top_selling_products"][0]["id"], self.prod_approved.pk)
        self.assertEqual(data["low_stock_products"][0]["id"], self.prod_low.pk)
        self.assertNotContains(response, "Outside Scope Product")
        self.assertNotContains(response, "OUTSIDE-ORDER")
        self.assertNotContains(response, "Outside Category")
        payload = self.client.get(reverse("admin_dashboard_page"), HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
        self.assertEqual(payload["period_sales_sum"], "300.00")
        self.assertEqual(sum(payload["sales_chart"]["sales"]), 300)

    def test_final_audit_period_status_completion_and_approval_statistics(self):
        MarketplaceOrder.objects.create(product=self.prod_approved, product_name='Unpaid completed', quantity=1,
            total_price=1000, status='completed', payment_status='unpaid')
        Product.objects.create(seller=self.seller, name='Rejected scoped item', price=10, approval_status='rejected')
        data = self.dashboard({'period': '7'}).context['marketplace']
        self.assertEqual(data['total_orders'], 3)
        self.assertEqual(data['order_completion_rate'], 66.7)
        self.assertEqual(sum(row['count'] for row in data['period_order_status']), 3)
        self.assertEqual((data['total_sales'], data['period_completed_count']), ('300.00', 1))
        self.assertEqual(data['product_approval_summary'], {'total': 3, 'pending': 0, 'approved': 2, 'rejected': 1})
        old = timezone.now() - timedelta(days=40)
        MarketplaceOrder.objects.filter(pk=self.order_completed.pk).update(created_at=old)
        data = self.dashboard({'period':'7'}).context['marketplace']
        self.assertEqual((data['total_orders'], data['order_completion_rate']), (2, 50.0))
        self.marketplace_admin.major = None
        self.marketplace_admin.save(update_fields=['major'])
        page = self.dashboard()
        data = page.context['marketplace']
        self.assertIsNone(data['order_completion_rate'])
        self.assertEqual(sum(row['count'] for row in data['period_order_status']), 0)
        self.assertEqual(data['product_approval_summary']['total'], 0)
        self.assertContains(page, 'No orders placed in this reporting period.')

    def test_final_audit_mobile_owner_labels_and_navigation(self):
        from api.models import CampusHubUser
        mobile = CampusHubUser.objects.create(username='audit-mobile-owner', email='audit@example.test',
            first_name='Mobile', last_name='Seller', password_hash='unused', department=self.program, major=self.major)
        product = Product.objects.create(mobile_seller=mobile, name='Mobile stock item', stock=1, price=10,
            approval_status='pending', department=self.program, major=self.major)
        page = self.dashboard()
        data = page.context['marketplace']
        self.assertEqual(next(row for row in data['pending_approvals'] if row['id']==product.pk)['seller'], 'Mobile Seller')
        self.assertEqual(next(row for row in data['low_stock_products'] if row['id']==product.pk)['seller'], 'Mobile Seller')
        self.assertNotContains(page, 'sellerOverviewTitle')
        self.assertEqual(data['seller_overview'], {'approved': 1, 'pending': 0, 'suspended': 0})
        for name in ('admin_products_page','admin_orders_page','admin_sellers_page','bundle_monitor_list'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        for row in data['recent_orders'] + data['low_stock_products'] + data['pending_approvals']:
            self.assertEqual(self.client.get(row['url']).status_code, 200, row['url'])

    def test_unassigned_and_missing_btled_major_fail_closed(self):
        for department in (self.program, None):
            self.marketplace_admin.department = department
            self.marketplace_admin.major = None
            self.marketplace_admin.save(update_fields=["department", "major"])
            data = self.dashboard().context["marketplace"]
            self.assertEqual((data["total_products"], data["total_orders"], data["total_sales"]), (0, 0, "0.00"))
            self.assertEqual(data["activities"], [])
            self.assertEqual(data["seller_overview"], {"approved": 0, "pending": 0, "suspended": 0})

    def test_explicit_product_scope_overrides_owner_scope_and_legacy_multi_item_is_excluded(self):
        self.outside_product.department = self.program
        self.outside_product.major = self.major
        self.outside_product.save(update_fields=["department", "major"])
        data = self.dashboard().context["marketplace"]
        self.assertEqual(data["total_products"], 3)
        self.assertEqual(data["total_sales"], "1,200.00")
        payload = self.client.get(reverse("admin_dashboard_page"), HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()
        self.assertEqual(payload["period_sales_sum"], "1200.00", "API decimal strings stay machine-readable")
        self.outside_order.customization = {"items": [{"product_name": "own"}, {"product_name": "unverified owner"}]}
        self.outside_order.save(update_fields=["customization"])
        data = self.dashboard().context["marketplace"]
        self.assertEqual(data["total_sales"], "300.00")
        self.assertNotIn(self.outside_order.pk, [row["id"] for row in data["recent_orders"]])

    def test_period_changes_revenue_ranking_and_recent_orders_not_operational_counts(self):
        old = timezone.now() - timedelta(days=40)
        MarketplaceOrder.objects.filter(pk=self.order_completed.pk).update(created_at=old, completed_at=old)
        recent = self.dashboard({"period": "7"}).context["marketplace"]
        long = self.dashboard({"period": "90"}).context["marketplace"]
        self.assertEqual((recent["total_orders"], recent["total_sales"], recent["top_selling_products"]), (1, "0.00", []))
        self.assertEqual((long["total_orders"], long["total_sales"]), (2, "300.00"))
        self.assertEqual(sum(row["count"] for row in recent["order_status"]), 2)
        self.assertEqual(recent["seller_overview"], long["seller_overview"])
        for grouping in ("weekly", "monthly"):
            grouped = self.dashboard({"period": "90", "grouping": grouping}).context["marketplace"]
            for key in ("total_sales", "top_selling_products", "product_categories", "seller_overview", "order_status"):
                self.assertEqual(grouped[key], long[key])

    def test_threshold_and_exact_variant_inventory_are_reused(self):
        self.prod_low.low_stock_threshold = 2
        self.prod_low.save(update_fields=["low_stock_threshold"])
        self.prod_approved.customization_enabled = True
        self.prod_approved.customization_options = [{"name": "Size", "options": [
            {"name": "Small", "stock": 10, "low_stock_threshold": 3},
            {"name": "Large", "stock": 1, "low_stock_threshold": 2}]}]
        self.prod_approved.save(update_fields=["customization_enabled", "customization_options"])
        rows = self.dashboard().context["marketplace"]["low_stock_products"]
        self.assertEqual([(row["variant_name"], row["stock"], row["threshold"]) for row in rows], [("Large", 1, 2)])

    def test_invalid_sales_do_not_enter_revenue_rankings_or_category_sales(self):
        for status, payment, quantity in (("pending", "paid", 1), ("cancelled", "paid", 1), ("completed", "unpaid", 1), ("completed", "paid", 0)):
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name="Invalid sale", quantity=quantity,
                total_price=1000, unit_price=1000, status=status, payment_status=payment)
        data = self.dashboard().context["marketplace"]
        self.assertEqual(data["total_sales"], "300.00")
        self.assertEqual(data["period_completed_count"], 1)
        self.assertEqual(len(data["top_selling_products"]), 1)
        self.assertEqual(sum(float(row["sales"].replace(",", "")) for row in data["product_categories"]["categories"]), 300)

    def test_activity_evidence_precedence_and_module_boundaries(self):
        own = self.event(product_id=self.prod_approved.pk)
        order = self.event("ORDER_UPDATED", "Marketplace Orders", order_id=self.order_completed.pk)
        self.event(product_id=self.outside_product.pk)
        self.event(product_id=self.prod_approved.pk, order_id=self.outside_order.pk)
        self.event(product_id=self.prod_approved.pk, major_id=self.other_major.pk)
        self.event()
        self.event("BOOKING_APPROVED", "Facilities", product_id=self.prod_approved.pk)
        self.event("ADMIN_SCOPE_CHANGED", "User Management")
        self.event("ACCOUNT_RECOVERY_INITIATED", "User Management")
        from accounts.support_scope import scope_marketplace_activity
        ids = set(scope_marketplace_activity(AccountActivity.objects.all(), self.marketplace_admin).values_list("pk", flat=True))
        self.assertEqual(ids, {own.pk, order.pk})
        data = self.dashboard().context["marketplace"]
        self.assertEqual(len(data["activities"]), 2)
        self.assertEqual(data["activities"][0]["performed_by"], self.marketplace_admin.username)

    def test_seller_suspension_and_unlinked_mobile_application_use_existing_scope(self):
        from api.models import CampusHubUser
        SellerRequest.objects.filter(user=self.seller).update(is_suspended=True)
        mobile = CampusHubUser.objects.create(username="scoped-mobile", student_id="scoped-mobile", first_name="Mobile", role="User",
            email="scoped-mobile@example.edu", department=self.program, major=self.major, password_hash="unused")
        SellerRequest.objects.create(student_id=mobile.username, full_name="Mobile Seller", product_type="Food", status="pending")
        self.assertEqual(self.dashboard().context["marketplace"]["seller_overview"], {"approved": 0, "pending": 1, "suspended": 1})

    def test_widgets_navigation_empty_states_and_super_api_protection(self):
        response = self.dashboard()
        content = response.content.decode()
        labels = ["Marketplace Overview", "Attention Required", "Sales Overview", "Sales Trend", "Top-Selling Products", "Recent Orders", "Inventory Alerts", "Recent Marketplace Activities"]
        offsets = [content.index(label, content.index('<main')) for label in labels]
        self.assertEqual(offsets, sorted(offsets))
        for label in ("Facility Utilization", "Upcoming Reservations", "Database Status", "Total Users", "Sample data for testing only"):
            self.assertNotContains(response, label)
        self.assertNotContains(response, "Order Status</h3>")
        self.assertContains(response, "No marketplace activities yet.")
        self.assertEqual(self.client.get(reverse("admin_dashboard_api")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin_bookings_page")).status_code, 302)
        self.assertEqual(self.client.get('/api/bookings/').status_code, 403)
        link = reverse("admin_orders_page") + f"?search={self.order_completed.order_code}&order={self.order_completed.pk}"
        linked = self.client.get(link)
        self.assertEqual(linked.status_code, 200)
        self.assertContains(linked, f'data-order-id="{self.order_completed.pk}"')
        forged = self.client.get(reverse("admin_orders_page"), {"order": self.outside_order.pk})
        self.assertNotContains(forged, "OUTSIDE-ORDER")

    def test_query_count_does_not_grow_per_low_stock_row_or_audit_event(self):
        with CaptureQueriesContext(connection) as baseline:
            self.dashboard()
        for index in range(20):
            product = Product.objects.create(seller=self.seller, name=f"Low product {index}", price=10, stock=1, low_stock_threshold=2)
            self.event(product_id=product.pk)
        with CaptureQueriesContext(connection) as populated:
            response = self.dashboard()
        self.assertLessEqual(len(populated), len(baseline) + 2)
        self.assertEqual(len(response.context["marketplace"]["activities"]), 5)
        self.assertEqual(len(response.context["marketplace"]["low_stock_products"]), 5)

    def test_attention_counts_are_scoped_complete_and_actionable(self):
        Product.objects.create(seller=self.seller, name="Awaiting review", price=10, stock=20, approval_status="pending")
        Product.objects.create(seller=self.seller, name="Sold out", price=10, stock=0, approval_status="approved")
        for index in range(8):
            Product.objects.create(seller=self.seller, name=f"Attention stock {index}", price=10, stock=1, low_stock_threshold=2, approval_status="approved")
        SellerRequest.objects.create(user=self.seller, student_id=self.seller.username, full_name="Scoped Applicant", product_type="Supplies", status="pending")
        response = self.dashboard({"period": "today"})
        attention = response.context["marketplace"]["attention_required"]
        items = {row["key"]: row for row in attention["items"]}
        self.assertEqual({key: row["count"] for key, row in items.items()}, {
            "low_stock_products": 9, "out_of_stock_products": 1, "pending_products": 1,
            "pending_sellers": 1, "pending_orders": 1})
        self.assertIn("inventory_status=low_stock", items["low_stock_products"]["url"])
        self.assertIn("status=pending", items["pending_products"]["url"])
        self.assertEqual(items["pending_orders"]["url"], reverse("admin_orders_page") + "?status=pending")
        self.assertTemplateUsed(response, "dashboard/partials/attention_required.html")
        self.assertContains(response, 'id="dashboardAttentionTitle"', count=1)
        for key in ("pending_bookings", "maintenance_facilities", "booking_conflicts", "backup_warning"):
            self.assertNotIn(key, items)
        self.assertEqual(self.dashboard({"period": "90", "grouping": "monthly"}).context["marketplace"]["attention_required"], attention)

    def test_attention_empty_and_missing_scope_do_not_show_zero_rows(self):
        Product.objects.filter(seller=self.seller).update(stock=20)
        MarketplaceOrder.objects.filter(pk=self.order_pending.pk).update(status="cancelled")
        response = self.dashboard()
        self.assertEqual(response.context["marketplace"]["attention_required"]["items"], [])
        self.assertContains(response, "No Items Require Attention")
        self.assertNotContains(response, 'data-attention-key=')
        self.marketplace_admin.major = None
        self.marketplace_admin.save(update_fields=["major"])
        response = self.dashboard()
        self.assertEqual(response.context["marketplace"]["attention_required"]["items"], [])

    def test_export_browser_review(self):
        destination = os.environ.get("MARKETPLACE_DASHBOARD_REVIEW_DIR")
        if not destination:
            return
        root = Path(destination)
        root.mkdir(parents=True, exist_ok=True)
        self.event(product_id=self.prod_approved.pk)
        self.order_pending.fulfillment_method='seller_delivery'
        self.order_pending.status='ready_for_pickup'
        self.order_pending.delivered_at=timezone.now()
        self.order_pending.inventory_deducted=True
        self.order_pending.save(update_fields=['fulfillment_method','status','delivered_at','inventory_deducted'])
        from api.models import BundleRecommendation
        a,b=sorted([self.prod_approved,self.prod_low],key=lambda p:p.pk)
        BundleRecommendation.objects.create(product_a=a,product_b=b)
        response = self.dashboard()
        root.joinpath("populated.html").write_bytes(response.content)
        for grouping in ('weekly','monthly'):
            root.joinpath(grouping+'.html').write_bytes(self.dashboard({'period':'90','grouping':grouping}).content)
        root.joinpath("order.html").write_bytes(self.client.get(reverse("admin_orders_page"),
            {"search": self.order_completed.order_code, "order": self.order_completed.pk}).content)
        root.joinpath("data.json").write_text(json.dumps(response.context["marketplace"], default=str), encoding="utf-8")
        Product.objects.filter(seller=self.seller).update(is_archived=True)
        MarketplaceOrder.objects.filter(product__seller=self.seller).delete()
        AccountActivity.objects.all().delete()
        root.joinpath("empty.html").write_bytes(self.dashboard().content)

    def test_dashboard_analytics_share_revenue_scope_period_and_legacy_exclusion(self):
        from modules.marketplace.services.analytics import build_marketplace_analytics
        buyer = User.objects.create_user(username='unrelated-buyer', department=self.program, major=self.other_major)
        self.order_completed.buyer_user_id = buyer.pk
        self.order_completed.save(update_fields=['buyer_user_id'])
        MarketplaceOrder.objects.create(product=self.prod_approved, product_name='Unverified legacy sale',
            quantity=10, total_price=5000, status='completed', payment_status='paid',
            customization={'items': [{'product_id': self.prod_approved.pk}, {'product_id': self.outside_product.pk}]})
        for grouping in ('daily', 'weekly', 'monthly'):
            params = {'period': '30', 'grouping': grouping}
            dashboard = self.dashboard(params).context['marketplace']
            analytics = build_marketplace_analytics(params, user=self.marketplace_admin)
            self.assertEqual(dashboard['total_sales'], analytics['kpis']['sales'])
            self.assertEqual(dashboard['period_completed_count'], analytics['kpis']['completed_orders'])
            self.assertEqual(dashboard['total_orders'], analytics['order_status_breakdown']['total'])
            self.assertEqual(dashboard['sales_chart']['sales'], analytics['sales_chart']['sales'])
            self.assertEqual(dashboard['total_sales'], '300.00')
            metrics = {row['key']: row['value'] for row in dashboard['sales_overview']['metrics']}
            self.assertEqual(metrics['average'], analytics['kpis']['average_order_value'])
        page = self.client.get(reverse('admin_marketplace_analytics_page'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, '<h1 class="header-page-title">Marketplace Analytics</h1>', html=True)

    def test_previews_limit_sort_and_inventory_depletion_with_real_records(self):
        for index in range(7):
            product = Product.objects.create(seller=self.seller, name=f'Preview {index}', price=10,
                stock=0 if index < 2 else 1, low_stock_threshold=3, approval_status='approved')
            MarketplaceOrder.objects.create(product=product, product_name=product.name, quantity=index + 1,
                total_price=10, status='completed', payment_status='paid')
            self.event(product_id=product.pk)
        data = self.dashboard().context['marketplace']
        self.assertEqual(len(data['recent_orders']), 5)
        self.assertEqual([r['id'] for r in data['recent_orders']], sorted([r['id'] for r in data['recent_orders']], reverse=True))
        self.assertEqual(len(data['activities']), 5)
        self.assertEqual(len(data['low_stock_products']), 5)
        self.assertEqual([r['stock'] for r in data['low_stock_products'][:2]], [0, 0])
        self.assertTrue(all(r['is_out_of_stock'] for r in data['low_stock_products'][:2]))
        self.assertEqual(len(data['top_selling_products']), 5)
        units = [r['units_sold'] for r in data['top_selling_products']]
        self.assertEqual(units, sorted(units, reverse=True))

    def test_marketplace_dates_preserve_year_and_general_auth_is_excluded(self):
        from datetime import datetime
        event = self.event(product_id=self.prod_approved.pk)
        local = timezone.localtime(timezone.now()).replace(month=10, day=23, hour=20, minute=20)
        AccountActivity.objects.filter(pk=event.pk).update(created_at=local)
        older = self.event(product_id=self.prod_approved.pk)
        AccountActivity.objects.filter(pk=older.pk).update(created_at=timezone.make_aware(datetime(local.year - 1, 12, 30, 16, 20)))
        self.event('LOGGED_IN', 'Authentication', product_id=self.prod_approved.pk)
        rows = self.dashboard().context['marketplace']['activities']
        self.assertEqual(rows[0]['date'], 'Oct 23, 8:20 PM')
        self.assertEqual(rows[1]['date'], f'Dec 30, {local.year - 1}, 4:20 PM')
        self.assertEqual(len(rows), 2)

    def test_category_revenue_matches_kpi_analytics_scope_and_recorded_categories(self):
        from modules.marketplace.services.analytics import build_marketplace_analytics
        MarketplaceOrder.objects.filter(product__seller=self.seller).delete()
        self.prod_approved.category = 'Current Catalog Category'
        self.prod_approved.save(update_fields=['category'])
        buyer = User.objects.create_user(username='category-outside-buyer', department=self.program, major=self.other_major)
        for category, quantity, unit in [('Recorded Sale Category', 3, 40), ('', 2, 25)]:
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name='Actual scoped product',
                buyer_user_id=buyer.pk, category=category, quantity=quantity, unit_price=unit,
                total_price=quantity * unit, status='completed', payment_status='paid')
        for status, payment in [('cancelled', 'paid'), ('completed', 'unpaid')]:
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name='Ineligible category sale',
                category='Excluded', quantity=1, unit_price=999, total_price=999, status=status, payment_status=payment)
        old = MarketplaceOrder.objects.create(product=self.prod_approved, product_name='Earlier sale',
            category='Earlier Category', quantity=1, unit_price=20, total_price=20, status='completed', payment_status='paid',
            completed_at=timezone.now() - timedelta(days=40))
        data = self.dashboard({'period': '7'}).context['marketplace']
        chart = data['category_sales_chart']
        self.assertEqual(chart['total_sales'], data['total_sales'])
        self.assertEqual(sum(chart['values']), 170)
        self.assertEqual(chart['labels'], ['Recorded Sale Category', 'Current Catalog Category'])
        self.assertAlmostEqual(sum(chart['percentages']), 100, places=1)
        analytics = build_marketplace_analytics({'period': '7'}, user=self.marketplace_admin)
        self.assertEqual([(r['name'], r['sales']) for r in chart['categories']],
                         [(r['category'], r['sales']) for r in analytics['category_sales']])
        self.assertEqual(self.dashboard({'period': '90'}).context['marketplace']['category_sales_chart']['total_sales'], '190.00')

    def test_category_donut_caps_slices_and_reconciles_others_without_extra_queries(self):
        from .dashboard_marketplace import category_sales_chart, sales_by_product_category
        from modules.marketplace.services.analytics import valid_sales_queryset
        MarketplaceOrder.objects.filter(product__seller=self.seller).delete()
        for index in range(7):
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                category=f'Category {index}', quantity=2, unit_price=(7-index)*50, total_price=(7-index)*100,
                status='completed', payment_status='paid')
        summary = sales_by_product_category(valid_sales_queryset(self.marketplace_admin))
        with self.assertNumQueries(0):
            chart = category_sales_chart(summary)
        self.assertEqual(chart['labels'], [f'Category {i}' for i in range(5)] + ['Others'])
        self.assertEqual(chart['values'], [700, 600, 500, 400, 300, 300])
        self.assertEqual(sum(chart['values']), 2800)
        self.assertEqual(chart['percentages'][-1], 10.7)
        self.assertNotContains(self.dashboard(), 'id="marketplaceCategorySalesChart"')
        # A genuine category called Others must not produce two indistinguishable slices.
        MarketplaceOrder.objects.filter(category='Category 0', product=self.prod_approved).update(category='Others')
        chart = self.dashboard().context['marketplace']['category_sales_chart']
        self.assertEqual(chart['labels'].count('Others'), 1)
        self.assertEqual(sum(chart['values']), 2800)

    def test_category_zero_sales_is_empty_not_a_fabricated_slice(self):
        MarketplaceOrder.objects.filter(product__seller=self.seller).delete()
        MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
            category='Zero Value Category', quantity=1, unit_price=0, total_price=0, status='completed', payment_status='paid')
        page = self.dashboard()
        self.assertEqual(page.context['marketplace']['category_sales_chart']['values'], [])
        self.assertNotContains(page, 'No Category Sales Yet')
        self.assertNotContains(page, 'No completed and paid orders in the selected period.')
        self.assertNotContains(page, 'id="marketplaceCategorySalesChart"')

    def test_final_layout_orders_sections_and_links_existing_destinations(self):
        page = self.dashboard()
        html = page.content.decode()
        anchors = ['marketplaceOverviewTitle', 'dashboard-attention', 'marketplaceRecommendationsTitle',
                   'salesOverviewTitle', 'recentMarketplaceOrdersTitle', 'inventoryAlertsTitle', 'marketplaceActivityTitle']
        positions = [html.index(anchor) for anchor in anchors]
        self.assertEqual(positions, sorted(positions))
        self.assertNotContains(page, 'sellerOverviewTitle')
        self.assertContains(page, 'class="marketplace-summary-left"')
        self.assertContains(page, 'Marketplace Revenue')
        self.assertContains(page, 'No Bundle Suggestions Yet')
        self.assertContains(page, 'Completed and paid marketplace orders')
        self.assertContains(page, 'class="marketplace-kpi-link"', count=4)

    def test_compact_dashboard_removes_only_redundant_displays(self):
        page = self.dashboard()
        self.assertNotContains(page, 'data-product-approval-summary')
        self.assertNotContains(page, 'sellerOverviewTitle')
        self.assertNotContains(page, 'marketplaceCategorySalesChart')
        self.assertContains(page, 'Pending Product Approvals')
        self.assertContains(page, 'Marketplace Sales')
        self.assertContains(page, 'View chart data')
        self.assertNotContains(page, 'No completed and paid orders in the selected period.')
        self.assertIn('product_approval_summary', page.context['marketplace'])
        self.assertIn('category_sales_chart', page.context['marketplace'])
        self.assertContains(page, '>Items</th>')
        for order in page.context['marketplace']['recent_orders']:
            self.assertIn('item_count', order)
            self.assertContains(page, order['url'])

    def test_empty_sales_have_one_shared_message_and_keep_real_comparisons(self):
        from datetime import datetime
        from decimal import Decimal
        from modules.marketplace.services.analytics import AnalyticsPeriod
        from .views import _sales_overview_summary
        from django.template.loader import render_to_string
        now = timezone.localdate()
        period = AnalyticsPeriod(key='30', label='Last 30 Days', start=now-timedelta(days=29), end=now)
        MarketplaceOrder.objects.all().delete()
        page = self.dashboard()
        self.assertContains(page, 'No completed and paid orders in the selected period.', count=1)
        self.assertContains(page, 'No Sales Data Yet', count=1)
        self.assertContains(page, 'No Top-Selling Products Yet', count=1)
        self.assertNotContains(page, 'No change')
        context = {key: page.context[key] for key in (
            'marketplace', 'sales_overview', 'sales_period_key', 'sales_period',
            'sales_days', 'sales_grouping', 'today', 'perms', 'user',
        )}
        # A real previous-period sale still warrants an accurate -100% comparison.
        earlier = timezone.make_aware(datetime.combine(period.start-timedelta(days=1), datetime.min.time()))
        MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
            quantity=1, total_price=100, status='completed', payment_status='paid', completed_at=earlier)
        from modules.marketplace.services.analytics import valid_sales_queryset
        context['sales_overview'] = _sales_overview_summary(valid_sales_queryset(self.marketplace_admin), period, Decimal('0'), 0)
        context['marketplace_compact'] = True
        content = render_to_string('dashboard/partials/sales_overview.html', context)
        self.assertEqual(content.count('No completed and paid orders in the selected period.'), 1)
        self.assertEqual(content.count('-100.0%'), 3)
        # Other callers retain the shared component's original comparison rendering.
        context['marketplace_compact'] = False
        original = render_to_string('dashboard/partials/sales_overview.html', context)
        self.assertNotIn('marketplace-sales-empty-summary', original)
        self.assertIn('No Category Sales Yet', original)

    def export_sales_trend_review(self, name, page):
        destination = os.environ.get('SALES_TREND_REVIEW_DIR')
        if destination:
            target = Path(destination); target.mkdir(parents=True, exist_ok=True)
            (target / (name + '.html')).write_bytes(page.content)
            data = page.context['marketplace']
            (target / (name + '.json')).write_text(json.dumps({**data['sales_chart'],
                'metrics':data['sales_overview']['metrics'], 'comparison':data['sales_overview'].get('comparison'),
                'products':data['top_selling_products'], 'date_error':data.get('date_range_error'),
                'has_sales':data['sales_overview']['has_sales']}, default=str), encoding='utf-8')

    def test_sales_trend_empty_hides_only_compact_legend_and_disclosure(self):
        from django.template.loader import render_to_string
        MarketplaceOrder.objects.all().delete()
        for status, payment, delivered in [('completed', 'unpaid', False), ('pending', 'paid', False), ('processing', 'paid', False),
                                            ('cancelled', 'paid', False), ('ready_for_pickup', 'unpaid', True)]:
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                quantity=1, total_price=500, status=status, payment_status=payment,
                fulfillment_method='seller_delivery' if delivered else 'pickup',
                delivered_at=timezone.now() if delivered else None)
        old = timezone.now() - timedelta(days=60)
        MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
            quantity=1, total_price=900, status='completed', payment_status='paid', completed_at=old)
        before = (MarketplaceOrder.objects.count(), AccountActivity.objects.count())
        page = self.dashboard()
        self.assertFalse(page.context['sales_overview']['has_sales'])
        self.assertEqual(page.context['marketplace']['total_sales'], '0.00')
        self.assertEqual(sum(page.context['marketplace']['sales_chart']['orders']), 0)
        self.assertEqual(len(page.context['sales_overview']['rows']), 30)
        self.assertContains(page, 'No Sales Data Yet', count=1)
        self.assertContains(page, 'Sales trends will appear when completed and paid orders are recorded in the selected period.', count=1)
        self.assertNotContains(page, 'class="sales-overview__legend sales-chart-legend"')
        self.assertNotContains(page, 'class="sales-overview__data"')
        self.assertEqual((MarketplaceOrder.objects.count(), AccountActivity.objects.count()), before)
        self.export_sales_trend_review('empty', page)
        context = {key: page.context[key] for key in ('marketplace', 'sales_overview', 'sales_period_key',
            'sales_period', 'sales_days', 'sales_grouping', 'today', 'perms', 'user')}
        # The shared component's other callers retain their legend and disclosure.
        original = render_to_string('dashboard/partials/sales_overview.html', context)
        self.assertIn('class="sales-overview__legend sales-chart-legend"', original)
        self.assertIn('class="sales-overview__data"', original)

    def test_sales_trend_populated_preserves_zero_dates_currency_period_and_grouping(self):
        from datetime import datetime, time
        from decimal import Decimal
        MarketplaceOrder.objects.all().delete()
        today = timezone.localdate()
        start, end = today - timedelta(days=4), today - timedelta(days=1)
        for day, total in [(start + timedelta(days=1), Decimal('0')), (end, Decimal('1250.50')),
                           (start - timedelta(days=1), Decimal('9000'))]:
            stamp = timezone.make_aware(datetime.combine(day, time(12)))
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                quantity=1, total_price=total, status='completed', payment_status='paid', completed_at=stamp)
        for grouping in ('daily', 'weekly', 'monthly'):
            with self.subTest(grouping=grouping):
                page = self.dashboard({'period': 'custom', 'date_from': start.isoformat(),
                    'date_to': end.isoformat(), 'grouping': grouping})
                overview, chart = page.context['sales_overview'], page.context['marketplace']['sales_chart']
                self.assertTrue(overview['has_sales'])
                self.assertEqual((overview['start'], overview['end']), (start, end))
                self.assertEqual(page.context['marketplace']['total_sales'], '1,250.50')
                self.assertEqual(sum(chart['orders']), 2)
                self.assertEqual(sum(chart['sales']), 1250.5)
                self.assertEqual(chart['grouping'], grouping)
                self.assertNotContains(page, 'class="sales-overview__legend sales-chart-legend"')
                self.assertContains(page, '<details class="sales-overview__data">', count=1)
                self.assertContains(page, 'View chart data')
                self.assertContains(page, '&#8369;1,250.50')
                self.assertNotContains(page, 'No Sales Data Yet')
                if grouping == 'daily':
                    self.assertEqual(chart['sales'], [0, 0, 0, 1250.5])
                    self.assertEqual(chart['orders'], [0, 1, 0, 1])
                    self.assertEqual([row['sales'] for row in overview['rows']], ['0.00', '0.00', '0.00', '1,250.50'])
                self.export_sales_trend_review('populated-' + grouping, page)

    def test_sales_trend_zero_price_completed_paid_order_is_not_empty(self):
        MarketplaceOrder.objects.all().delete()
        MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
            quantity=1, total_price=0, status='completed', payment_status='paid', completed_at=timezone.now())
        page = self.dashboard()
        self.assertTrue(page.context['sales_overview']['has_sales'])
        self.assertEqual(page.context['marketplace']['total_sales'], '0.00')
        self.assertEqual(sum(page.context['marketplace']['sales_chart']['orders']), 1)
        self.assertContains(page, '<details class="sales-overview__data">')
        self.assertNotContains(page, 'No Sales Data Yet')
        self.export_sales_trend_review('zero-price', page)

    def test_delivery_preview_preserves_unpaid_open_state_and_legacy_unknown_method(self):
        self.order_pending.fulfillment_method = 'seller_delivery'
        self.order_pending.status = 'ready_for_pickup'
        self.order_pending.delivered_at = timezone.now()
        self.order_pending.save(update_fields=['fulfillment_method','status','delivered_at'])
        page = self.dashboard()
        data = page.context['marketplace']
        preview = next(row for row in data['recent_orders'] if row['id'] == self.order_pending.pk)
        self.assertEqual(preview['fulfillment']['fulfillment_progress'], 'Delivered')
        self.assertEqual(preview['payment_key'], 'unpaid')
        self.assertEqual(data['total_sales'], '300.00')
        self.assertContains(page, 'Awaiting payment')
        self.assertContains(page, 'Ready for Seller Delivery')
        self.assertContains(page, 'Not recorded')
        self.order_pending.refresh_from_db()
        self.assertEqual((self.order_pending.status,self.order_pending.payment_status), ('ready_for_pickup','unpaid'))

    def test_inventory_alert_reserved_units_match_exact_variant(self):
        self.prod_approved.customization_enabled = True
        self.prod_approved.customization_options = [{'name':'Size','options':[
            {'name':'Small','stock':2,'extra_price':0}, {'name':'Large','stock':3,'extra_price':0}]}]
        self.prod_approved.save(update_fields=['customization_enabled','customization_options'])
        MarketplaceOrder.objects.create(product=self.prod_approved, quantity=2, total_price=10,
            status='pending', payment_status='unpaid', inventory_deducted=True, customization={'selections':[{'group':'Size','option':'Small'}]})
        rows = [row for row in self.dashboard().context['marketplace']['low_stock_products'] if row['id']==self.prod_approved.pk]
        self.assertEqual({row['variant_name']:row['stock'] for row in rows}, {'Small':2,'Large':3})
        self.assertEqual({row['variant_name']:row['reserved'] for row in rows}, {'Small':2,'Large':0})

    def test_activity_links_use_authorized_existing_records_only(self):
        self.event('ORDER_UPDATED','Marketplace Orders',order_id=self.order_completed.pk)
        rows = self.dashboard().context['marketplace']['activities']
        self.assertTrue(any(row['url']==reverse('admin_orders_page')+f'?order={self.order_completed.pk}' for row in rows))

    def test_marketplace_average_distinguishes_undefined_from_real_zero_and_positive(self):
        MarketplaceOrder.objects.all().delete()
        for name, amount in [('empty', None), ('zero', 0), ('positive', 1250.50)]:
            if amount is not None:
                MarketplaceOrder.objects.all().delete()
                MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                    quantity=1, total_price=amount, status='completed', payment_status='paid', completed_at=timezone.now())
            page = self.dashboard()
            metric = page.context['sales_overview']['metrics'][2]
            average_html = re.search(r'<article[^>]*data-metric="average".*?</article>',page.content.decode(),re.S).group()
            self.assertEqual(metric['comparison']['defined'], amount is not None)
            value = {'empty': '&mdash;', 'zero': '&#8369;0.00', 'positive': '&#8369;1,250.50'}[name]
            self.assertInHTML(f'<strong>{value}</strong>',average_html)
            self.assertIsNone(metric['comparison']['change'])
            self.assertContains(page, 'No eligible completed and paid orders are available for this average.', count=1 if amount is None else 0)
            self.export_sales_trend_review('average-' + name, page)

    def test_marketplace_comparisons_reuse_one_aggregate_and_actual_equivalent_dates(self):
        from datetime import date
        from decimal import Decimal
        from modules.reports.views import _sales_overview_summary
        from modules.marketplace.services.analytics import AnalyticsPeriod, valid_sales_queryset
        from unittest.mock import patch
        today = date(2026, 10, 26)
        MarketplaceOrder.objects.all().delete()
        for days, amount in [(0, 300), (30, 40), (31, 60)]:
            stamp = timezone.make_aware(datetime.combine(today - timedelta(days=days), time(12)))
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                quantity=1, total_price=amount, status='completed', payment_status='paid', completed_at=stamp)
        with self.assertNumQueries(1):
            overview = _sales_overview_summary(valid_sales_queryset(self.marketplace_admin),
                AnalyticsPeriod('30', 'Last 30 Days', today-timedelta(days=29), today), Decimal(300), 1, marketplace=True)
        self.assertEqual([r['comparison']['previous'] for r in overview['metrics']], ['100.00', '2', '50.00'])
        self.assertEqual([r['comparison']['change'] for r in overview['metrics']], ['+200.0%', '-50.0%', '+500.0%'])
        with patch('modules.reports.views.timezone.localdate', return_value=today):
            for key, start, end, days in [('month', date(2026,9,5), date(2026,9,30),26),
                                           ('year',date(2025,3,8),date(2025,12,31),299)]:
                page = self.dashboard({'period':key})
                self.assertEqual(page.context['sales_overview']['comparison'], {'start':start,'end':end,'days':days})
                self.assertNotContains(page, 'vs. previous month')
                self.assertNotContains(page, 'vs. previous year')
                self.export_sales_trend_review('comparison-' + key, page)
        page = self.dashboard()
        self.export_sales_trend_review('comparison-positive', page)

    def test_marketplace_custom_date_validation_and_explicit_safe_fallback(self):
        from datetime import date
        from unittest.mock import patch
        today = date(2026,10,26)
        invalid = [({}, 'Enter valid start and end dates.'),
            ({'date_from':'2026-02-30','date_to':'2026-10-26'}, 'Enter valid start and end dates.'),
            ({'date_from':'invalid','date_to':'2026-10-26'}, 'Enter valid start and end dates.'),
            ({'date_from':'2026-10-26','date_to':'2026-10-25'}, 'Start date must be on or before end date.'),
            ({'date_from':'2026-10-25','date_to':'2026-10-27'}, 'End date cannot be in the future.'),
            ({'date_from':'1900-01-01','date_to':'2026-10-26'}, 'Choose a range of at most 3,661 days, starting in 1900 or later.'),
            ({'date_from':'1899-01-01','date_to':'1899-01-02'}, 'Choose a range of at most 3,661 days, starting in 1900 or later.')]
        with patch('modules.reports.views.timezone.localdate', return_value=today):
            for index, (params, message) in enumerate(invalid):
                with self.subTest(params=params):
                    page = self.client.get(reverse('admin_dashboard_page'), {'period':'custom',**params})
                    self.assertEqual(page.status_code,400)
                    self.assertContains(page,message,status_code=400)
                    self.assertContains(page,'The requested range was not applied. Showing Last 30 Days.',status_code=400)
                    self.assertEqual(page.context['sales_period'].days,30)
                    ajax = self.client.get(reverse('admin_dashboard_page'), {'period':'custom',**params},HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    self.assertEqual((ajax.status_code,ajax.json()), (400,{'error':message}))
                    if index == 1: self.export_sales_trend_review('invalid-dates',page)
            for days in [1,3661]:
                start = today-timedelta(days=days-1)
                page = self.dashboard({'period':'custom','date_from':start.isoformat(),'date_to':today.isoformat()})
                self.assertEqual(page.context['sales_period'].days,days)
                self.assertEqual(page.context['marketplace']['date_range_error'],'')
            for key in ['today','7','14','30','90','month','year']:
                self.assertEqual(self.dashboard({'period':key}).context['sales_period_key'],key)

    def test_marketplace_recognition_boundaries_are_philippine_local(self):
        from datetime import datetime, timezone as dt_timezone
        MarketplaceOrder.objects.all().delete()
        for stamp, amount in [('2026-10-25T15:59:59+00:00',10),('2026-10-25T16:00:00+00:00',20),
                              ('2026-10-26T15:59:59+00:00',30),('2026-10-26T16:00:00+00:00',40)]:
            MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                quantity=1,total_price=amount,status='completed',payment_status='paid',
                completed_at=datetime.fromisoformat(stamp))
        with timezone.override(dt_timezone.utc):
            page = self.dashboard({'period':'custom','date_from':'2026-10-26','date_to':'2026-10-26'})
        data = page.context['marketplace']
        self.assertEqual((data['total_sales'],data['period_completed_count']),('50.00',2))
        self.assertEqual(data['sales_chart']['sales'],[50.0])
        self.assertEqual(data['sales_overview']['metrics'][0]['comparison']['previous'],'10.00')

    def test_marketplace_top_five_details_use_authorized_batched_ownership(self):
        from unittest.mock import patch
        MarketplaceOrder.objects.all().delete()
        products=[]
        for index in range(7):
            product=Product.objects.create(seller=self.seller,name=f'Ranked product {index}',price=10,stock=10)
            products.append(product)
            MarketplaceOrder.objects.create(product=product,product_name=product.name,quantity=index+1,total_price=(index+1)*10,
                seller_name='Recorded Seller' if index==6 else '',status='completed',payment_status='paid',completed_at=timezone.now())
        MarketplaceOrder.objects.create(product=self.outside_product,product_name='Outside Scope Product',quantity=100,total_price=9999,
            status='completed',payment_status='paid',completed_at=timezone.now())
        page=self.dashboard()
        rows=page.context['marketplace']['top_selling_products']
        self.assertEqual([r['id'] for r in rows],[p.pk for p in reversed(products[2:])])
        self.assertEqual(rows[0]['seller_name'],'Recorded Seller')
        self.assertEqual(rows[1]['seller_name'],self.seller.get_full_name() or self.seller.username)
        table=re.search(r'<table[^>]*marketplace-top-products-table.*?</table>',page.content.decode(),re.S).group()
        self.assertEqual(re.findall(r'<th scope="col"[^>]*>(.*?)</th>',table),['Product','Seller','Units Sold','Sales Revenue'])
        self.assertEqual(table.count('<tr>'),6)
        self.assertEqual(len(re.findall(r'<a\b',table)),5)
        self.assertNotContains(page,'Outside Scope Product')
        self.assertContains(page,'&#8369;70.00')
        for row in rows:
            self.assertEqual(self.client.get(row['product_url']).status_code,200)
        self.export_sales_trend_review('top-five',page)
        MarketplaceOrder.objects.filter(product=products[-1]).update(seller_name='Not Assigned')
        self.assertEqual(self.dashboard().context['marketplace']['top_selling_products'][0]['seller_name'],'Not Assigned')
        with patch('modules.marketplace.services.product_access.admin_product_queryset',return_value=Product.objects.none()):
            denied=self.dashboard()
        self.assertTrue(all(not row['product_url'] for row in denied.context['marketplace']['top_selling_products']))
        table=re.search(r'<table[^>]*marketplace-top-products-table.*?</table>',denied.content.decode(),re.S).group()
        self.assertNotRegex(table,r'<a\b')
