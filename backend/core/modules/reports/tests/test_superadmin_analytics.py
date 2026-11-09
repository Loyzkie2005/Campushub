# Original location: backend/core/modules/reports/test_superadmin_analytics.py
"""Automated test suite for CampusHub Super Admin Analytics Module.

Covers:
1. Super Admin authorization and scoped RBAC across all 4 tabs (Marketplace, Facilities, Services, Users).
2. Shared date range filtering (7, 30, 90, year, custom, invalid custom dates).
3. Marketplace sales revenue aggregation: completed and paid orders, regardless of recorded fulfillment.
4. Facilities booking metrics: approved, pending, cancelled, bookings by facility.
5. Services analytics: authentic registered service resources, request breakdowns, honest empty states.
6. Users analytics: total registrations, period registrations, distribution by role, seller status.
7. Empty database handling and zero-activity periods.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.tests import test_admin_workflows as fixtures
from accounts.models import Department, Role, User
from api.models import Booking, CampusHubUser, Facility, MarketplaceOrder, Product, SellerRequest


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SuperAdminAnalyticsTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 19)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return

        Booking.objects.all().delete()
        MarketplaceOrder.objects.all().delete()
        Product.objects.all().delete()

        # Physical facility
        self.court = Facility.objects.create(
            id="FAC-COURT-TEST",
            facility_name="Covered Court",
            facility_type="court",
            booking_mode="hourly",
        )
        # Service facility
        self.lab = Facility.objects.create(
            id="FAC-LAB-TEST",
            facility_name="Food Analysis Hub",
            facility_type="food_analysis",
            booking_mode="service",
        )

        self.seller_user = User.objects.create_user(
            username="seller-verified",
            password=self.password,
            email="seller.verified@ustp.edu.ph",
            role="Seller",
        )

        self.product = Product.objects.create(
            seller=self.seller_user,
            name="USTP Uniform Polo",
            price=Decimal("450.00"),
            stock=25,
            approval_status=Product.STATUS_APPROVED,
        )

    def test_super_admin_can_access_all_four_tabs(self):
        """Super Admin has full access to Marketplace, Facilities, Services, and Users tabs."""
        self.client.force_login(self.super_admin)
        url = reverse("admin_marketplace_analytics_page")

        for module in ("marketplace", "facilities", "services", "users"):
            response = self.client.get(url, {"module": module})
            self.assertEqual(response.status_code, 200, f"Super Admin should access {module} tab")
            self.assertContains(response, f"data-analytics-module=\"{module}\"")
            self.assertContains(response, "Marketplace")
            self.assertContains(response, "Facilities")
            self.assertContains(response, "Services")
            self.assertContains(response, "Users")

    def test_marketplace_admin_restricted_from_other_tabs(self):
        """Marketplace Admin can only access marketplace tab; facilities, services, users return 403."""
        self.client.force_login(self.marketplace_admin)
        url = reverse("admin_marketplace_analytics_page")

        mp_res = self.client.get(url, {"module": "marketplace"})
        self.assertEqual(mp_res.status_code, 200)

        for module in ("facilities", "services", "users"):
            res = self.client.get(url, {"module": module})
            self.assertEqual(res.status_code, 403, f"Marketplace Admin must be blocked from {module}")

    def test_unauthenticated_redirect(self):
        """Unauthenticated requests redirect to login."""
        self.client.logout()
        url = reverse("admin_marketplace_analytics_page")
        for module in ("marketplace", "facilities", "services", "users"):
            res = self.client.get(url, {"module": module})
            self.assertEqual(res.status_code, 302)

    def test_shared_date_filters(self):
        """All valid presets (7, 30, 90, year, custom) resolve cleanly without server error."""
        self.client.force_login(self.super_admin)
        url = reverse("admin_marketplace_analytics_page")

        for period in ("7", "30", "90", "year"):
            res = self.client.get(url, {"module": "marketplace", "period": period})
            self.assertEqual(res.status_code, 200)

        # Valid custom range
        res = self.client.get(url, {
            "module": "marketplace",
            "period": "custom",
            "date_from": "2026-10-01",
            "date_to": "2026-10-15",
        })
        self.assertEqual(res.status_code, 200)

        # Invalid custom range returns 400
        bad_res = self.client.get(url, {
            "module": "marketplace",
            "period": "custom",
            "date_from": "invalid",
            "date_to": "dates",
        })
        self.assertEqual(bad_res.status_code, 400)

        # start_date > end_date returns 400
        inverted_res = self.client.get(url, {
            "module": "marketplace",
            "period": "custom",
            "date_from": "2026-10-20",
            "date_to": "2026-10-10",
        })
        self.assertEqual(inverted_res.status_code, 400)

    def test_marketplace_sales_revenue_derives_only_from_settled_completed_orders(self):
        """Completed & paid orders count towards revenue; cancelled or unpaid orders do not."""
        self.client.force_login(self.super_admin)
        now = timezone.now()

        # Qualifying completed & paid order: 2 units * 450 = 900
        order_completed = MarketplaceOrder.objects.create(
            buyer_user_id=self.marketplace_admin.pk,
            product=self.product,
            product_name=self.product.name,
            quantity=2,
            unit_price=Decimal("450.00"),
            total_price=Decimal("900.00"),
            status=MarketplaceOrder.STATUS_COMPLETED,
            payment_status=MarketplaceOrder.PAYMENT_PAID,
            completed_at=now,
            paid_at=now,
        )

        # Pending order: not completed or paid
        order_pending = MarketplaceOrder.objects.create(
            buyer_user_id=self.marketplace_admin.pk,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            unit_price=Decimal("450.00"),
            total_price=Decimal("450.00"),
            status=MarketplaceOrder.STATUS_PENDING,
            payment_status=MarketplaceOrder.PAYMENT_UNPAID,
        )

        # Cancelled order
        order_cancelled = MarketplaceOrder.objects.create(
            buyer_user_id=self.marketplace_admin.pk,
            product=self.product,
            product_name=self.product.name,
            quantity=3,
            unit_price=Decimal("450.00"),
            total_price=Decimal("1350.00"),
            status=MarketplaceOrder.STATUS_CANCELLED,
            payment_status=MarketplaceOrder.PAYMENT_UNPAID,
        )

        res = self.client.get(reverse("admin_marketplace_analytics_page"), {"module": "marketplace", "period": "30"})
        self.assertEqual(res.status_code, 200)
        analytics = res.context["analytics"]

        # Only order_completed should be included in total sales revenue
        self.assertEqual(analytics["kpis"]["sales"], "900.00")
        self.assertEqual(analytics["kpis"]["completed_orders"], 1)
        self.assertEqual(analytics["kpis"]["approved_products"], 1)

    def test_facilities_analytics_counts_approved_and_pending_bookings(self):
        """Facilities KPI cards accurately reflect real booking statuses."""
        self.client.force_login(self.super_admin)
        now = timezone.now()

        # Approved reservation (within last 30 days)
        b_approved = Booking.objects.create(
            id="B-APP-01",
            facility=self.court,
            user=self.ch_user,
            booking_date=self.today,
            start_time=time(8, 0),
            end_time=time(10, 0),
            status=Booking.STATUS_APPROVED,
            total_amount=Decimal("200.00"),
        )
        Booking.objects.filter(pk=b_approved.pk).update(created_at=now)

        # Pending reservation (within last 30 days)
        b_pending = Booking.objects.create(
            id="B-PEN-01",
            facility=self.court,
            user=self.ch_user,
            booking_date=self.today - timedelta(days=2),
            start_time=time(10, 0),
            end_time=time(12, 0),
            status=Booking.STATUS_PENDING,
            total_amount=Decimal("200.00"),
        )
        Booking.objects.filter(pk=b_pending.pk).update(created_at=now)

        # Cancelled reservation (within last 30 days)
        b_cancelled = Booking.objects.create(
            id="B-CAN-01",
            facility=self.court,
            user=self.ch_user,
            booking_date=self.today - timedelta(days=5),
            start_time=time(14, 0),
            end_time=time(16, 0),
            status=Booking.STATUS_CANCELLED,
            total_amount=Decimal("200.00"),
        )
        Booking.objects.filter(pk=b_cancelled.pk).update(created_at=now)

        res = self.client.get(reverse("admin_marketplace_analytics_page"), {"module": "facilities", "period": "30"})
        self.assertEqual(res.status_code, 200)
        facility_tab = res.context["facility_tab"]

        self.assertEqual(facility_tab["kpis"]["total_bookings"], 3)
        self.assertEqual(facility_tab["kpis"]["approved_bookings"], 1)
        self.assertEqual(facility_tab["kpis"]["pending_bookings"], 1)
        self.assertEqual(facility_tab["kpis"]["cancelled_rejected_bookings"], 1)
        self.assertEqual(facility_tab["most_frequent"]["name"], "Covered Court")

    def test_services_analytics_registered_resources_and_honest_empty_states(self):
        """Services tab displays registered BEU resources without fake charts or fabricated data."""
        self.client.force_login(self.super_admin)
        res = self.client.get(reverse("admin_marketplace_analytics_page"), {"module": "services", "period": "30"})
        self.assertEqual(res.status_code, 200)
        services_tab = res.context["services_tab"]

        self.assertGreaterEqual(len(services_tab["services"]), 1)
        self.assertEqual(services_tab["kpis"]["registered_services"], len(services_tab["services"]))
        # With zero service requests submitted, honest empty states are reported
        self.assertEqual(services_tab["kpis"]["total_requests"], 0)
        self.assertContains(res, "Laboratory Food Analysis")
        self.assertContains(res, "DPM-USTP-Oro-BEU-004")

    def test_users_analytics_registration_and_distribution(self):
        """Users tab aggregates registration dates, role distributions, and seller applications."""
        self.client.force_login(self.super_admin)
        SellerRequest.objects.create(
            user=self.seller_user,
            student_id="2023302222",
            status=SellerRequest.STATUS_APPROVED,
        )

        res = self.client.get(reverse("admin_marketplace_analytics_page"), {"module": "users", "period": "30"})
        self.assertEqual(res.status_code, 200)
        users_tab = res.context["users_tab"]

        self.assertGreaterEqual(users_tab["kpis"]["total_users"], 3)
        self.assertGreaterEqual(users_tab["kpis"]["approved_sellers"], 1)
        self.assertEqual(users_tab["seller_stats"]["approved"], 1)

    def analytics_page(self, module='marketplace', **params):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('admin_marketplace_analytics_page'), {'module': module, **params})
        self.assertEqual(response.status_code, 200)
        return response

    def test_marketplace_sections_operational_cohort_and_recorded_variants(self):
        stamp = timezone.make_aware(datetime(2026, 10, 6, 12))
        options = {'selections': [{'group': 'Size', 'option': 'Large'}, {'group': 'Color', 'option': 'Navy'}]}
        records = [
            self.sale('100', stamp, quantity=2, customization=options, fulfillment_method='pickup'),
            self.sale('90', stamp + timedelta(hours=2), quantity=3, customization=options, fulfillment_method='seller_delivery'),
            self.sale('50', None, payment_status='unpaid'),
            self.sale('60', None, status='processing', payment_status='unpaid', fulfillment_method='seller_delivery', delivered_at=stamp),
            self.sale('20', None, status='cancelled', payment_status='unpaid', fulfillment_method='pickup'),
            self.sale('20', None, status='pending', payment_status='legacy'),
        ]
        MarketplaceOrder.objects.filter(pk__in=[r.pk for r in records]).update(created_at=stamp - timedelta(hours=2))
        earlier = self.sale('40', stamp)
        MarketplaceOrder.objects.filter(pk=earlier.pk).update(created_at=stamp - timedelta(days=40))
        before = MarketplaceOrder.objects.count()
        page = self.analytics_page(period='custom', date_from='2026-10-01', date_to='2026-10-19')
        data = page.context['analytics']; operations = data['operations']
        self.assertEqual((operations['total'], operations['completed'], operations['cancelled']), (6, 3, 1))
        self.assertEqual((operations['completion_rate'], operations['cancellation_rate']), (50.0, 16.7))
        self.assertEqual((operations['timed'], operations['processing_hours']), (2, 3.0))
        self.assertEqual([r['count'] for r in operations['payment']], [2, 3, 1])
        self.assertEqual([r['count'] for r in operations['fulfillment']], [2, 2, 2])
        self.assertEqual(data['kpis']['sales'], '230.00')
        combined = next(r for r in data['variant_sales'] if 'Size: Large' in r['variant'])
        self.assertEqual((combined['orders'], combined['units'], combined['sales']), (2, 5, '190.00'))
        self.assertEqual(data['seller_fulfillment'][0]['completed'], 3)
        self.assertEqual(MarketplaceOrder.objects.count(), before)
        for heading in ('Marketplace Overview', 'Sales &amp; Revenue Analysis', 'Orders &amp; Payments Analytics', 'Product &amp; Inventory Analytics',
                        'Buyers &amp; Sellers Analytics', 'Marketplace Insights &amp; Recommendations'):
            self.assertContains(page, heading)
        import re
        self.assertEqual(re.findall(r'data-marketplace-section="([^"]+)"', page.content.decode()),
                         ['overview', 'sales', 'orders', 'products', 'people', 'insights'])
        self.assertContains(page, '<summary>View order volume data</summary>', html=True)
        self.assertNotContains(page, '>Decision Support<')
        empty = self.analytics_page(period='custom', date_from='2026-09-01', date_to='2026-09-02').context['analytics']
        self.assertIsNone(empty['operations']['completion_rate'])
        self.assertIsNone(empty['operations']['processing_hours'])
        self.assertEqual(empty['variant_sales'], [])
        self.assertEqual(empty['kpis']['approved_products'], data['kpis']['approved_products'])

    def test_marketplace_unit_turnover_requires_continuous_observed_history(self):
        from api.models import InventorySKU, InventoryStockMovement
        stamp = timezone.make_aware(datetime(2026, 10, 16, 12))
        order = self.sale('100', stamp, quantity=2)
        sku = InventorySKU.objects.get(product=self.product, group_name='', variant_name='')
        opening = InventoryStockMovement.objects.create(sku=sku, kind='opening', balance='on_hand',
            quantity_change=10, available_before=0, available_after=10)
        InventoryStockMovement.objects.filter(pk=opening.pk).update(created_at=stamp - timedelta(days=20))
        movement = InventoryStockMovement.objects.create(sku=sku, order=order, kind='sale', balance='on_hand',
            quantity_change=-2, available_before=10, available_after=8)
        InventoryStockMovement.objects.filter(pk=movement.pk).update(created_at=stamp)
        from modules.reports.superadmin_analytics import marketplace_stock_turnover
        from modules.marketplace.services.analytics import AnalyticsPeriod, valid_sales_queryset
        period = AnalyticsPeriod('custom', 'October', date(2026, 10, 1), date(2026, 10, 31))
        rows = marketplace_stock_turnover(Product.objects.filter(pk=self.product.pk), valid_sales_queryset(), period)
        self.assertEqual((rows[0]['average_stock'], rows[0]['units'], rows[0]['turnover']), (9.0, 2, 0.22))
        self.assertEqual(rows[0]['sell_through'], 20.0)
        InventoryStockMovement.objects.filter(pk=movement.pk).update(available_before=9)
        self.assertIsNone(marketplace_stock_turnover(Product.objects.filter(pk=self.product.pk), valid_sales_queryset(), period)[0]['turnover'])
        InventoryStockMovement.objects.filter(pk=movement.pk).update(available_before=10)
        ambiguous = InventoryStockMovement.objects.create(sku=sku, kind='adjustment', balance='available',
            quantity_change=1, available_before=8, available_after=9)
        InventoryStockMovement.objects.filter(pk=ambiguous.pk).update(created_at=stamp + timedelta(hours=1))
        self.assertIsNone(marketplace_stock_turnover(Product.objects.filter(pk=self.product.pk), valid_sales_queryset(), period)[0]['sell_through'])
        InventoryStockMovement.objects.filter(pk=opening.pk).delete()
        self.assertIsNone(marketplace_stock_turnover(Product.objects.filter(pk=self.product.pk), valid_sales_queryset(), period)[0]['turnover'])

    def test_marketplace_processing_excludes_invalid_completion_and_get_is_read_only(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from api.models import InventorySKU, InventoryStockMovement
        stamp = timezone.make_aware(datetime(2026, 10, 6, 12))
        order = self.sale('10', stamp)
        MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=stamp + timedelta(hours=1))
        before = (MarketplaceOrder.objects.count(), InventorySKU.objects.count(), InventoryStockMovement.objects.count())
        self.client.force_login(self.super_admin)
        with CaptureQueriesContext(connection) as queries:
            page = self.client.get(reverse('admin_marketplace_analytics_page'),
                {'period': 'custom', 'date_from': '2026-10-01', 'date_to': '2026-10-19'})
        self.assertEqual(page.status_code, 200)
        self.assertIsNone(page.context['analytics']['operations']['processing_hours'])
        self.assertEqual(before, (MarketplaceOrder.objects.count(), InventorySKU.objects.count(), InventoryStockMovement.objects.count()))
        self.assertFalse(any(q['sql'].lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER')) for q in queries))

    def test_marketplace_sections_query_count_does_not_grow_per_order(self):
        import json, os
        from pathlib import Path
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from modules.marketplace.services.analytics import build_marketplace_analytics
        from modules.reports.superadmin_analytics import enrich_marketplace
        stamp = timezone.make_aware(datetime(2026, 10, 6, 12))
        self.sale('10', stamp)
        params = {'period': 'custom', 'date_from': '2026-10-01', 'date_to': '2026-10-19'}
        counts = []
        for size in (1, 51):
            if size == 51:
                for _ in range(50):
                    self.sale('10', stamp)
            with CaptureQueriesContext(connection) as queries:
                analytics = build_marketplace_analytics(params, user=self.super_admin, refined=True)
                enrich_marketplace(analytics, self.super_admin)
            counts.append(len(queries))
        self.assertEqual(counts[0], counts[1])
        directory = os.environ.get('MARKETPLACE_SECTIONS_REVIEW_DIR') or os.environ.get('MARKETPLACE_REFINEMENT_REVIEW_DIR')
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            (target/'query-count.json').write_text(json.dumps({'orders': [1, 51], 'queries': counts}), encoding='utf-8')

    def test_marketplace_refinement_keeps_pending_volume_with_zero_recognized_sales(self):
        stamp = timezone.make_aware(datetime(2026, 10, 6, 12))
        for _ in range(3):
            row = self.sale('50', None, status='pending', payment_status='unpaid', fulfillment_method='pickup')
            MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=stamp)
        page = self.analytics_page(period='custom', date_from='2026-10-01', date_to='2026-10-19')
        data = page.context['analytics']
        self.assertEqual(data['kpis']['sales'], '0.00')
        self.assertEqual(data['operations']['total'], 3)
        self.assertEqual(sum(data['order_volume']['chart']['values']), 3)
        self.assertContains(page, 'id="marketplaceOrderVolumeChart"')
        self.assertNotContains(page, 'id="marketplaceSalesChart"')
        self.assertContains(page, 'Product Association Analytics')
        self.assertNotContains(page, 'Frequently Bought Together')
        self.assertNotContains(page, 'Seller Sales Ranking')
        self.assertContains(page, 'Insufficient verified stock history', count=1)
        self.assertEqual(data['variant_sales'], [])

    def test_order_volume_groupings_fill_zeros_without_changing_cohort(self):
        for day, status, payment, amount in [
            (date(2026, 10, 1), 'pending', 'unpaid', '50'),
            (date(2026, 10, 1), 'cancelled', 'unpaid', '20'),
            (date(2026, 10, 19), 'completed', 'paid', '100'),
            (date(2026, 9, 30), 'pending', 'unpaid', '15'),
            (date(2026, 10, 20), 'completed', 'paid', '200'),
        ]:
            stamp = timezone.make_aware(datetime.combine(day, time(12)))
            order = self.sale(amount, stamp if status == 'completed' else None, status=status, payment_status=payment)
            MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=stamp)
        for grouping, expected in [('daily', None), ('weekly', [2, 0, 0, 1]), ('monthly', [3]), ('invalid', None)]:
            page = self.analytics_page(period='custom', date_from='2026-10-01', date_to='2026-10-19', grouping='weekly', order_grouping=grouping)
            data = page.context['analytics']; volume = data['order_volume']
            self.assertEqual((data['operations']['total'], data['operations']['completed'], data['operations']['cancelled']), (3, 1, 1))
            self.assertEqual((data['operations']['completion_rate'], data['operations']['cancellation_rate']), (33.3, 33.3))
            self.assertEqual(data['kpis']['sales'], '100.00')
            self.assertEqual(data['grouping'], 'weekly')
            self.assertEqual(data['submission_comparison']['rows'][0]['current'], 3)
            self.assertEqual(sum(volume['chart']['values']), 3)
            if expected is None:
                self.assertEqual(volume['grouping'], 'daily')
                self.assertEqual(len(volume['chart']['values']), 19)
                self.assertEqual(volume['chart']['values'].count(0), 17)
            else:
                self.assertEqual(volume['chart']['values'], expected)
        monthly = self.analytics_page(period='custom', date_from='2026-08-01', date_to='2026-10-19', order_grouping='monthly').context['analytics']['order_volume']
        self.assertEqual(monthly['chart']['values'], [0, 1, 3])
        from modules.reports.superadmin_analytics import request_demand
        legacy = request_demand(MarketplaceOrder.objects.filter(created_at__date__range=(date(2026, 10, 1), date(2026, 10, 19))), data['period'])
        self.assertEqual(legacy['chart']['values'], [2, 1])
        self.assertNotIn('grouping', legacy)
        empty = self.analytics_page(period='custom', date_from='2025-01-01', date_to='2025-01-03')
        self.assertEqual(empty.context['analytics']['order_volume']['chart']['values'], [0, 0, 0])
        self.assertContains(empty, 'Average Fulfillment Time')
        self.assertNotContains(empty, 'id="marketplaceOrderVolumeChart"')

    def test_marketplace_refinement_groups_stable_seller_ids_without_collapsing_matching_names(self):
        now = timezone.now()
        self.seller_user.first_name = 'Same'; self.seller_user.last_name = 'Seller'
        self.seller_user.save(update_fields=['first_name', 'last_name'])
        other = User.objects.create_user(username='same-name-web', first_name='Same', last_name='Seller')
        mobile = CampusHubUser.objects.create(username='same-name-mobile', email='same-mobile@example.test',
            password_hash='isolated-test-hash', first_name='Same', last_name='Seller', user_type='student')
        for seller, key in [(self.seller_user, 'source-a'), (other, 'source-b')]:
            SellerRequest.objects.create(user=seller, student_id=key, status='approved')
        SellerRequest.objects.create(mobile_user=mobile, student_id='source-mobile', status='approved')
        web_product = Product.objects.create(seller=other, name='Other web product', price=20, stock=20, approval_status='approved')
        first = Product.objects.create(mobile_seller=mobile, name='Mobile first', price=100, stock=20, approval_status='approved')
        second = Product.objects.create(mobile_seller=mobile, name='Mobile second', price=200, stock=20, approval_status='approved')
        for product, amount in [(self.product, 10), (web_product, 20), (first, 100), (second, 200)]:
            row = MarketplaceOrder.objects.create(product=product, product_name=product.name, total_price=amount,
                quantity=1, status='completed', payment_status='paid', completed_at=now)
            MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=now - timedelta(hours=1))
        data = self.analytics_page(period='30').context['analytics']
        sellers = data['seller_performance']['rows']; fulfillment = data['seller_fulfillment']
        expected = {f'web:{self.seller_user.pk}', f'web:{other.pk}', f'mobile:{mobile.pk}'}
        self.assertEqual({r['seller_key'] for r in sellers}, expected)
        self.assertEqual(len(sellers), 3)
        self.assertEqual({r['seller_key'] for r in fulfillment}, expected)
        self.assertEqual(len(fulfillment), 3)
        row = next(r for r in sellers if r['seller_key'] == f'mobile:{mobile.pk}')
        self.assertEqual((row['sales'], row['orders'], row['units'], row['rank']), ('300.00', 2, 2, 1))
        self.assertIn('q=same-name-mobile', row['search_url'])
        self.assertEqual(next(r for r in fulfillment if r['seller_key'] == row['seller_key'])['total'], 2)

    def test_marketplace_refined_association_panel_uses_existing_detailed_rule_counts(self):
        from django.template.loader import render_to_string
        from modules.marketplace.services.analytics import calculate_market_basket
        # Isolated algorithm inputs; no transaction or synthetic result is injected into a live page.
        transactions = [[(1, 'A'), (2, 'B')], [(1, 'A'), (2, 'B')], [(1, 'A')]]
        result = calculate_market_basket(transactions, detailed=True)
        row = next(r for r in result['rows'] if r['product_a_id'] == 1)
        self.assertEqual((row['support'], row['confidence'], row['lift']), (66.67, 66.67, 1.0))
        self.assertEqual((row['together_count'], row['source_count'], row['target_count']), (2, 3, 2))
        html = render_to_string('reports/partials/marketplace_refined_panels.html', {'card': 'association', 'analytics': {'market_basket': result}})
        for label in ('Support (%)', 'Confidence (%)', 'Lift', 'Together', 'A Transactions', 'B Transactions'):
            self.assertIn(label, html)

    def test_forecast_observed_history_exact_moving_average_and_future_exclusion(self):
        from modules.marketplace.services.analytics import AnalyticsPeriod, _forecast
        today = self.today
        for offset in range(14):
            self.sale('10', timezone.make_aware(datetime.combine(today - timedelta(days=offset), time(12))), quantity=2)
        # Bad future-dated records must not enter the observed training window.
        self.sale('999', timezone.make_aware(datetime.combine(today + timedelta(days=1), time(12))), quantity=999)
        period = AnalyticsPeriod('semester', 'Observed semester', date(2026, 8, 1), date(2026, 12, 31))
        result = _forecast(self.product, period, 7, 3, user=self.super_admin, today=today)
        self.assertTrue(result['sufficient'])
        self.assertEqual((result['history_days'], result['units'], result['eligible_orders']), (14, 28, 14))
        self.assertEqual((result['forecast_total'], result['suggested_preparation']), (14, 11))
        self.assertEqual(result['chart']['forecast'][-7:], [2.0] * 7)
        self.assertEqual(result['observed_end'], today)
        for offset in range(7):
            MarketplaceOrder.objects.filter(completed_at__date=today - timedelta(days=offset)).update(quantity=7 - offset)
        varied = _forecast(self.product, period, 7, 3, today=today)
        self.assertEqual(varied['chart']['forecast'][-7:-4], [4.0, 4.43, 4.78])
        self.assertEqual(varied['forecast_total'], 34)

    def test_forecast_rejects_short_observation_and_stale_demand(self):
        from modules.marketplace.services.analytics import AnalyticsPeriod, _forecast
        period = AnalyticsPeriod('30', 'Last 30 Days', self.today - timedelta(days=29), self.today)
        for offset in range(3):
            self.sale('10', timezone.make_aware(datetime.combine(self.today - timedelta(days=offset), time(12))), quantity=3)
        result = _forecast(self.product, period, 7, 3, today=self.today)
        self.assertFalse(result['sufficient'])
        self.assertEqual(result['history_days'], 3)
        self.product.submitted_at = timezone.make_aware(datetime.combine(period.start, time(8)))
        self.assertTrue(_forecast(self.product, period, 7, 3, today=self.today)['sufficient'])
        for index, order in enumerate(MarketplaceOrder.objects.order_by('pk')):
            MarketplaceOrder.objects.filter(pk=order.pk).update(completed_at=timezone.make_aware(datetime.combine(self.today - timedelta(days=20 + index), time(12))))
        result = _forecast(self.product, period, 7, 3, today=self.today)
        self.assertFalse(result['sufficient'])
        self.assertEqual(result['recent_units'], 0)
        self.assertEqual(result['sales_days'], 3)

    def test_restock_separates_historical_threshold_and_expiry_review(self):
        self.product.stock = 3; self.product.save(update_fields=['stock'])
        for offset in range(14):
            self.sale('10', timezone.make_aware(datetime.combine(self.today - timedelta(days=offset), time(12))), quantity=2)
        with patch('django.utils.timezone.localdate', return_value=self.today):
            page = self.analytics_page(period='30')
        data = page.context['analytics']
        self.assertTrue(data['restock']['forecast_ready'])
        self.assertEqual((data['forecast']['current_stock'], data['forecast']['suggested_preparation']), (3, 11))
        self.assertEqual(data['restock']['threshold_alerts'], 1)
        self.assertContains(page, 'Forecast-based:'); self.assertContains(page, 'Threshold-based:')
        with patch('django.utils.timezone.localdate', return_value=self.today + timedelta(days=1)):
            historical = self.analytics_page(period='custom', date_from='2026-10-06', date_to='2026-10-19')
        self.assertTrue(historical.context['analytics']['restock']['historical'])
        self.assertFalse(historical.context['analytics']['restock']['forecast_ready'])
        self.product.category = 'Snacks'; self.product.expiry_date = self.today - timedelta(days=1)
        self.product.save(update_fields=['category', 'expiry_date'])
        with patch('django.utils.timezone.localdate', return_value=self.today):
            expired = self.analytics_page(period='30').context['analytics']
        self.assertTrue(expired['restock']['inventory_review'])
        self.assertFalse(expired['restock']['forecast_ready'])
        self.product.expiry_date = None; self.product.category = 'Uniforms'; self.product.customization_enabled = True
        self.product.customization_options = [{'name':'Size', 'options':[{'value':'Small', 'stock':1}, {'value':'Large', 'stock':20}]}]
        self.product.save(update_fields=['expiry_date', 'category', 'customization_enabled', 'customization_options'])
        with patch('django.utils.timezone.localdate', return_value=self.today):
            variants = self.analytics_page(period='30').context['analytics']
        self.assertEqual(variants['forecast']['current_stock'], 21)
        self.assertTrue(variants['restock']['inventory_review'])
        self.assertFalse(variants['restock']['forecast_ready'])

    def test_shared_submission_populations_and_comparisons_match_dashboard(self):
        from uuid import uuid4
        from api.models import FacilityBookingRequest
        from modules.marketplace.services.analytics import AnalyticsPeriod
        from modules.reports.analytics_sections import build_facility_tab_analytics, build_services_tab_analytics
        from modules.reports.dashboard_executive import executive_overview, service_overview
        period = AnalyticsPeriod('custom', 'Ten days', date(2026, 10, 10), date(2026, 10, 19))
        for index, (facility, day, status) in enumerate([(self.court, 12, 'approved'), (self.court, 13, 'pending'),
                (self.court, 2, 'completed'), (self.lab, 12, 'completed'), (self.lab, 2, 'pending')]):
            row = Booking.objects.create(id=f'cohort-{index}', facility=facility, status=status)
            Booking.objects.filter(pk=row.pk).update(created_at=timezone.make_aware(datetime(2026, 10, day, 12)))
        block = Booking.objects.create(id='cohort-block', facility=self.court, status='approved')
        Booking.objects.filter(pk=block.pk).update(created_at=timezone.make_aware(datetime(2026, 10, 12, 12)))
        FacilityBookingRequest.objects.create(booking=block, request_key=uuid4(), details={'source':'schedule'})
        self.court.is_archived = True; self.court.save(update_fields=['is_archived'])
        facilities = build_facility_tab_analytics(period, {}, user=self.super_admin)
        services = build_services_tab_analytics(period, {}, user=self.super_admin)
        comparison = {'previous_start_date': date(2026, 9, 30), 'previous_end_date': date(2026, 10, 9), 'comparison_label':'Previous ten days'}
        dashboard = executive_overview(period, comparison)
        service_dashboard = service_overview(period)
        row = facilities['submission_comparison']['rows'][0]
        self.assertEqual((row['current'], row['previous'], row['difference'], row['change']), (2, 1, 1, '+100.0%'))
        self.assertEqual(row['current'], dashboard['booking_overview']['total'])
        self.assertEqual(sum(facilities['demand']['chart']['values']), row['current'])
        self.assertEqual(services['submission_comparison']['rows'][0]['current'], service_dashboard['total_requests'])
        self.assertEqual(sum(services['demand']['chart']['values']), service_dashboard['total_requests'])

    def test_registration_definition_matches_dashboard_and_semester_is_historical(self):
        from modules.marketplace.services.analytics import AnalyticsPeriod, parse_analytics_period
        from modules.reports.analytics_sections import build_users_tab_analytics
        from modules.reports.dashboard_executive import users_overview
        period = AnalyticsPeriod('custom', 'Ten days', date(2026, 10, 10), self.today)
        stamp = timezone.make_aware(datetime(2026, 10, 12, 12))
        User.objects.all().update(date_joined=stamp - timedelta(days=100))
        CampusHubUser.objects.all().update(created_at=stamp - timedelta(days=100))
        User.objects.create_user(username='shared-register', date_joined=stamp)
        CampusHubUser.objects.filter(pk=self.ch_user.pk).update(created_at=stamp)
        data = build_users_tab_analytics(period, {}, user=self.super_admin)
        summary = users_overview(period)
        self.assertEqual((data['kpis']['new_registrations'], sum(data['main_chart']['values']), summary['new_registrations']), (2, 2, 2))
        self.assertEqual(parse_analytics_period({'period':'semester'}, today=self.today).end, self.today)
        prior = parse_analytics_period({'period':'semester'}, today=date(2026, 5, 1))
        self.assertEqual((prior.start, prior.end), (date(2025, 8, 1), date(2025, 12, 31)))

    def test_live_associations_never_fall_back_to_synthetic_research(self):
        for _ in range(4):
            self.sale('10', timezone.now())
        with patch('modules.marketplace.services.bundle_suggestions._cached_synthetic', side_effect=AssertionError('Research must stay separate')):
            data = self.analytics_page(period='30').context['analytics']
        self.assertEqual(data['market_basket']['eligible_orders'], 4)
        self.assertEqual(data['market_basket']['multi_item_orders'], 0)
        self.assertFalse(data['market_basket']['sufficient'])

    def test_revenue_row_uses_paid_categories_zero_intervals_and_equivalent_growth(self):
        stamp = timezone.make_aware(datetime(2026, 10, 10, 12))
        for amount, category in [('120', 'Books'), ('80', 'Food'), ('40', 'Books')]:
            self.sale(amount, stamp, category=category)
        self.sale('500', stamp, payment_status='unpaid', category='Unpaid category')
        self.sale('120', stamp - timedelta(days=20), category='Previous category')
        for grouping in ('daily', 'weekly', 'monthly'):
            page = self.analytics_page(period='custom', date_from='2026-10-01', date_to='2026-10-19', grouping=grouping)
            data = page.context['analytics']
            self.assertEqual(data['kpis']['sales'], '240.00')
            self.assertEqual(sum(data['sales_chart']['sales']), 240)
            self.assertEqual([(r['category'], r['sales'], r['percent']) for r in data['category_sales']],
                             [('Books', '160.00', 66.7), ('Food', '80.00', 33.3)])
            self.assertEqual(data['comparison']['sales']['percentage_change'], 100.0)
            self.assertEqual(data['comparison']['previous_sales'], '120.00')
            self.assertEqual(data['revenue_aov'], {'current': '80.00', 'previous': '120.00', 'percentage_change': -33.33})
            self.assertContains(page, '<h3>Average Order Value</h3>', html=True)
            self.assertContains(page, '<dd>-33.3%</dd>', html=True)
            self.assertContains(page, '<h3>Sales Trend</h3>', html=True)
            self.assertContains(page, 'id="marketplaceCategorySummary"')
            self.assertNotContains(page, 'Monthly Sales Performance')
            if grouping == 'daily':
                self.assertEqual(len(data['sales_chart']['sales']), 19)
                self.assertEqual(data['sales_chart']['sales'].count(0), 18)
        empty = self.analytics_page(period='custom', date_from='2025-01-01', date_to='2025-01-07')
        self.assertContains(empty, 'aria-label="Revenue percentage change">N/A')
        self.assertNotContains(empty, 'id="marketplaceCategoryChart"')
        self.assertNotContains(empty, 'id="marketplaceSalesChart"')
        self.assertEqual(empty.context['analytics']['revenue_aov'], {'current': None, 'previous': None, 'percentage_change': None})

    def test_slow_moving_excludes_new_recently_approved_and_future_products(self):
        start = self.today - timedelta(days=29)
        old_stamp = timezone.make_aware(datetime.combine(start - timedelta(days=15), time(12)))
        Product.objects.filter(pk=self.product.pk).update(submitted_at=old_stamp, approved_at=old_stamp)
        aged = Product.objects.create(seller=self.seller_user, name='Established candidate', price=10, stock=10, approval_status='approved')
        fresh = Product.objects.create(seller=self.seller_user, name='Recent listing', price=10, stock=10, approval_status='approved')
        reviewed = Product.objects.create(seller=self.seller_user, name='Recent approval', price=10, stock=10, approval_status='approved')
        Product.objects.filter(pk=aged.pk).update(submitted_at=old_stamp, approved_at=old_stamp)
        Product.objects.filter(pk=fresh.pk).update(submitted_at=timezone.make_aware(datetime.combine(self.today, time(12))))
        Product.objects.filter(pk=reviewed.pk).update(submitted_at=old_stamp, approved_at=timezone.make_aware(datetime.combine(self.today, time(12))))
        for offset in range(5):
            self.sale('10', timezone.make_aware(datetime.combine(start + timedelta(days=offset), time(12))))
        for day in (start - timedelta(days=5), self.today + timedelta(days=5)):
            MarketplaceOrder.objects.create(product=aged, product_name=aged.name, quantity=1, total_price=10,
                status='completed', payment_status='paid', completed_at=timezone.make_aware(datetime.combine(day, time(12))))
        data = self.analytics_page(period='custom', date_from=start.isoformat(), date_to=self.today.isoformat()).context['analytics']
        self.assertTrue(data['slow_moving']['sufficient'])
        self.assertEqual([row['product'] for row in data['slow_moving']['rows']], ['Established candidate'])
        self.assertEqual(data['slow_moving']['history_excluded'], 2)
        self.assertEqual(data['slow_moving']['rows'][0]['last_sale'].date(), start - timedelta(days=5))
        Product.objects.filter(pk__in=[aged.pk, self.product.pk]).update(submitted_at=timezone.make_aware(datetime.combine(self.today, time(12))))
        insufficient = self.analytics_page(period='custom', date_from=start.isoformat(), date_to=self.today.isoformat()).context['analytics']['slow_moving']
        self.assertFalse(insufficient['sufficient'])
        self.assertEqual(insufficient['rows'], [])
        self.assertIn('Insufficient product history', insufficient['rule'])

    def test_revenue_aov_distinguishes_missing_orders_from_zero_value_orders(self):
        params = {'period': 'custom', 'date_from': '2026-10-01', 'date_to': '2026-10-07'}
        current = timezone.make_aware(datetime(2026, 10, 3, 12))
        prior = current - timedelta(days=7)
        current_order = self.sale('100', current)
        page = self.analytics_page(**params)
        self.assertEqual(page.context['analytics']['revenue_aov'], {'current': '100.00', 'previous': None, 'percentage_change': None})
        self.sale('0', prior)
        page = self.analytics_page(**params)
        self.assertEqual(page.context['analytics']['revenue_aov'], {'current': '100.00', 'previous': '0.00', 'percentage_change': None})
        self.assertContains(page, 'Previous AOV is zero')
        self.sale('100', prior)
        page = self.analytics_page(**params)
        self.assertEqual(page.context['analytics']['revenue_aov'], {'current': '100.00', 'previous': '50.00', 'percentage_change': 100.0})
        empty = self.analytics_page(period='custom', date_from='2026-10-08', date_to='2026-10-14')
        self.assertEqual(empty.context['analytics']['revenue_aov'], {'current': None, 'previous': '100.00', 'percentage_change': None})
        self.assertContains(empty, 'aria-label="Current-period average order value">N/A')
        MarketplaceOrder.objects.filter(pk=current_order.pk).update(total_price=0)
        zero = self.analytics_page(**params)
        self.assertEqual(zero.context['analytics']['revenue_aov'], {'current': '0.00', 'previous': '50.00', 'percentage_change': -100.0})
        self.assertContains(zero, 'aria-label="Current-period average order value">&#8369;0.00')

    def test_optional_marketplace_refinement_exports(self):
        import json, os
        from pathlib import Path
        target = os.environ.get('MARKETPLACE_REFINEMENT_REVIEW_DIR')
        if not target: return
        target = Path(target); target.mkdir(parents=True, exist_ok=True)
        today = date(2026, 10, 19); stamp = timezone.make_aware(datetime.combine(today, time(12)))
        for state in ('empty', 'pending', 'populated', 'standard'):
            if state == 'pending':
                row = self.sale('50', None, status='pending', payment_status='unpaid', fulfillment_method='pickup')
                MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=stamp)
            if state == 'populated':
                SellerRequest.objects.create(user=self.seller_user, student_id='refined-seller', status='approved')
                # Two approved identities exercise the existing multi-row ranking sort.
                self.seller_user.first_name = 'Verified'; self.seller_user.last_name = 'Seller'
                self.seller_user.save(update_fields=['first_name', 'last_name'])
                other = User.objects.create_user(username='ranking-review-other', first_name='Verified', last_name='Seller')
                SellerRequest.objects.create(user=other, student_id='ranking-review-other', status='approved')
                other_product = Product.objects.create(seller=other, name='ZZ Sorting Fixture', price=20, stock=20, approval_status='approved')
                Product.objects.filter(pk=other_product.pk).update(submitted_at=stamp, updated_at=stamp)
                for offset in range(7):
                    row = self.sale('90', stamp - timedelta(days=offset), quantity=3, buyer_user_id=self.ch_user.pk,
                        fulfillment_method='pickup' if offset % 2 else 'seller_delivery',
                        customization={'selections': [{'group': 'Size', 'option': 'Large'}]})
                    MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=stamp - timedelta(days=offset, hours=2))
                self.product.stock = 3; self.product.save(update_fields=['stock'])
            if state == 'standard':
                MarketplaceOrder.objects.update(customization={}, option='')
            for label, params in [('30', {'period':'30'}), ('7', {'period':'7'}),
                    ('custom', {'period':'custom', 'date_from':'2026-10-18', 'date_to':'2026-10-19'}),
                    ('weekly', {'period':'30', 'grouping':'weekly'}), ('horizon', {'period':'30','forecast_horizon':'30'})]:
                with patch('django.utils.timezone.localdate', return_value=today):
                    page = self.analytics_page(**params)
                (target/f'{state}-{label}.html').write_bytes(page.content)
                (target/f'{state}-{label}.json').write_text(json.dumps(page.context['analytics'], default=str), encoding='utf-8')

    def test_service_demand_completion_and_verified_timing(self):
        from uuid import uuid4
        from api.models import FacilityBookingRequest
        from modules.reports.analytics_sections import build_services_tab_analytics
        from modules.marketplace.services.analytics import AnalyticsPeriod
        start = timezone.make_aware(datetime(2026, 10, 1, 9))
        for index, status in enumerate(('completed', 'completed', 'pending')):
            booking = Booking.objects.create(id=f'service-timing-{index}', facility=self.lab, status=status)
            Booking.objects.filter(pk=booking.pk).update(created_at=start, updated_at=start + timedelta(days=4))
            if index == 0:
                FacilityBookingRequest.objects.create(booking=booking, request_key=uuid4(), details={
                    'approval': {'at': (start + timedelta(hours=2)).isoformat()},
                    'completion': {'at': (start + timedelta(hours=24)).isoformat()}})
        period = AnalyticsPeriod('custom', 'Selected dates', date(2026, 10, 1), date(2026, 10, 2))
        data = build_services_tab_analytics(period, {}, user=self.super_admin)
        self.assertEqual(data['performance'], {'approval_hours': 2.0, 'approval_timed': 1,
            'completion_hours': 24.0, 'completion_timed': 1, 'completion_rate': 66.7})
        self.assertEqual(sum(data['demand']['chart']['values']), 3)
        self.assertEqual(sum(data['demand']['weekday_chart']['values']), 3)
        self.assertEqual(len(data['pending']), 1)
        self.assertIn('q=service-timing-2', data['pending'][0]['url'])
        empty = build_services_tab_analytics(AnalyticsPeriod('custom', 'Empty', date(2026, 9, 1), date(2026, 9, 2)), {}, user=self.super_admin)
        self.assertIsNone(empty['performance']['completion_rate'])
        self.assertIsNone(empty['performance']['completion_hours'])

    def test_facility_approval_submission_scope_and_recorded_timestamps(self):
        from uuid import uuid4
        from api.models import FacilityBookingRequest
        from modules.reports.analytics_sections import build_facility_tab_analytics
        from modules.marketplace.services.analytics import AnalyticsPeriod
        stamp = timezone.make_aware(datetime(2026, 10, 1, 9))
        for index, status in enumerate(('approved', 'rejected', 'pending')):
            row = Booking.objects.create(id=f'approval-scope-{index}', facility=self.court,
                booking_date=date(2026, 10, 6), status=status)
            Booking.objects.filter(pk=row.pk).update(created_at=stamp)
            if index == 0:
                FacilityBookingRequest.objects.create(booking=row, request_key=uuid4(), details={'approval': {'at': (stamp + timedelta(hours=3)).isoformat()}})
        service = Booking.objects.create(id='exclude-service-demand', facility=self.lab, status='pending')
        Booking.objects.filter(pk=service.pk).update(created_at=stamp)
        data = build_facility_tab_analytics(AnalyticsPeriod('custom', 'Two days', date(2026, 10, 1), date(2026, 10, 2)), {}, user=self.super_admin)
        self.assertEqual(data['kpis']['total_bookings'], 0)
        self.assertEqual((data['approval']['total'], data['approval']['rate'], data['approval']['pending']), (3, 50.0, 1))
        self.assertEqual((data['approval']['approval_hours'], data['approval']['approval_timed']), (3.0, 1))
        self.assertEqual(sum(data['demand']['chart']['values']), 3)

    def test_user_verification_growth_and_observed_engagement(self):
        from accounts.models import AccountActivity
        from modules.reports.analytics_sections import build_users_tab_analytics
        from modules.marketplace.services.analytics import AnalyticsPeriod
        old = timezone.make_aware(datetime(2026, 8, 1, 9))
        stamp = timezone.make_aware(datetime(2026, 10, 2, 9))
        User.objects.all().update(date_joined=old, email_verified=False)
        CampusHubUser.objects.all().update(created_at=old, email_verified=False)
        User.objects.create_user(username='growth-current', date_joined=stamp, email_verified=True)
        User.objects.create_user(username='growth-previous', date_joined=stamp - timedelta(days=2))
        for source, account, result in [('admin', self.super_admin, 'success'), ('admin', self.super_admin, 'success'),
                ('mobile', self.ch_user, 'success'), ('mobile', self.ch_user, 'failed')]:
            event = AccountActivity.objects.create(account_source=source, account_id=account.pk,
                activity_type='login_success', activity='Recorded sign-in', result=result)
            AccountActivity.objects.filter(pk=event.pk).update(created_at=stamp)
        for index in range(2):
            row = Booking.objects.create(id=f'engaged-request-{index}', facility=self.lab, user=self.ch_user)
            Booking.objects.filter(pk=row.pk).update(created_at=stamp)
        data = build_users_tab_analytics(AnalyticsPeriod('custom', 'Two days', date(2026, 10, 1), date(2026, 10, 2)), {}, user=self.super_admin)
        self.assertEqual(data['verification']['verified'], 1)
        self.assertEqual(data['growth']['previous'], 1)
        self.assertEqual(data['kpis']['new_registrations'], 1)
        self.assertEqual(data['engagement'], {'signin_accounts': 2, 'signin_events': 3, 'request_accounts': 1})

    def test_optional_complete_analytics_exports(self):
        import json, os
        from pathlib import Path
        from uuid import uuid4
        from api.models import FacilityBookingRequest, FacilityPayment
        target = os.environ.get('ANALYTICS_COMPLETE_REVIEW_DIR')
        if not target:
            return
        target = Path(target); target.mkdir(parents=True, exist_ok=True)
        today = date(2026, 10, 19); stamp = timezone.make_aware(datetime(2026, 10, 18, 10))
        User.objects.all().update(date_joined=stamp - timedelta(days=100))
        CampusHubUser.objects.all().update(created_at=stamp - timedelta(days=100))
        for state in ('empty', 'populated'):
            if state == 'populated':
                SellerRequest.objects.create(user=self.seller_user, student_id='complete-analytics-seller', status='approved')
                for offset in range(14):
                    row = self.sale('90', stamp - timedelta(days=offset), quantity=3, buyer_user_id=self.ch_user.pk,
                        fulfillment_method='pickup' if offset % 2 else 'seller_delivery')
                    MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=stamp - timedelta(days=offset, hours=2))
                self.product.stock = 3; self.product.category = 'Uniforms'
                self.product.save(update_fields=['stock', 'category'])
                # Actual isolated test records cover category ordering, long labels and palette cycling.
                for index, category in enumerate(('Stationery', 'Books', 'Food', 'Apparel', 'Equipment', 'Artwork',
                        'Campus Research Materials & Technical Supplies', 'Learning Resources')):
                    amount = 15 * (index + 1)
                    product = Product.objects.create(seller=self.seller_user, name=f'Review product {index}',
                        category=category, price=amount, stock=20, approval_status='approved')
                    row = MarketplaceOrder.objects.create(product=product, product_name=product.name, category=category,
                        total_price=amount, quantity=1, status='completed', payment_status='paid', completed_at=stamp)
                    MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=stamp - timedelta(hours=2))
                self.court.facility_type = 'covered_court'; self.court.workflow_config = {'operating_hours': 'Daily 08:00-18:00'}
                self.court.save(update_fields=['facility_type', 'workflow_config'])
                for index, (facility, status) in enumerate([(self.court, 'approved'), (self.court, 'pending'), (self.lab, 'completed'), (self.lab, 'pending')]):
                    row = Booking.objects.create(id=f'complete-analytics-{index}', facility=facility, user=self.ch_user,
                        booking_date=today, start_time=time(8), end_time=time(10), status=status)
                    Booking.objects.filter(pk=row.pk).update(created_at=stamp)
                    details = {'approval': {'at': (stamp + timedelta(hours=2)).isoformat()}} if status in ('approved', 'completed') else {}
                    if status == 'completed':
                        details['completion'] = {'at': (stamp + timedelta(hours=24)).isoformat()}
                    FacilityBookingRequest.objects.create(booking=row, request_key=uuid4(), details=details)
                    if index == 0:
                        FacilityPayment.objects.create(id='complete-analytics-payment', booking=row, payment_status='paid', paid_amount=125, paid_at=stamp)
                User.objects.create_user(username='complete-new-user', date_joined=stamp, email_verified=True)
            for module in ('marketplace', 'facilities', 'services', 'users'):
                cases = [('30', {'period': '30'}), ('7', {'period': '7'}),
                        ('custom', {'period': 'custom', 'date_from': '2026-10-18', 'date_to': '2026-10-19'})]
                if module == 'marketplace':
                    cases += [('weekly', {'period':'30', 'grouping':'weekly'}), ('monthly', {'period':'30', 'grouping':'monthly'}),
                              ('orders-weekly', {'period':'30', 'order_grouping':'weekly'}),
                              ('orders-monthly', {'period':'30', 'order_grouping':'monthly'}),
                              ('orders-custom-monthly', {'period':'custom', 'date_from':'2026-10-18', 'date_to':'2026-10-19', 'order_grouping':'monthly'}),
                              ('horizon', {'period':'30', 'forecast_horizon':'30'})]
                for label, params in cases:
                    with patch('django.utils.timezone.localdate', return_value=today):
                        page = self.analytics_page(module, **params)
                    (target/f'{state}-{module}-{label}.html').write_bytes(page.content)
                    key = {'marketplace': 'analytics', 'facilities': 'facility_tab', 'services': 'services_tab', 'users': 'users_tab'}[module]
                    (target/f'{state}-{module}-{label}.json').write_text(json.dumps(page.context[key], default=str), encoding='utf-8')

    def test_optional_marketplace_sections_browser_exports(self):
        import json, os
        from pathlib import Path
        target = os.environ.get('MARKETPLACE_SECTIONS_REVIEW_DIR')
        if not target:
            return
        target = Path(target); target.mkdir(parents=True, exist_ok=True)
        today = date(2026, 10, 19)
        for state in ('empty', 'populated'):
            if state == 'populated':
                SellerRequest.objects.create(user=self.seller_user, student_id='sections-seller', status='approved')
                for index in range(7):
                    stamp = timezone.make_aware(datetime.combine(today - timedelta(days=index), time(12)))
                    row = self.sale('90', stamp, quantity=3, buyer_user_id=self.ch_user.pk,
                        fulfillment_method='pickup' if index % 2 else 'seller_delivery',
                        customization={'selections': [{'group': 'Size', 'option': 'Large'}]})
                    MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=stamp - timedelta(hours=2))
                open_order = self.sale('50', None, status='processing', payment_status='unpaid', fulfillment_method='seller_delivery')
                MarketplaceOrder.objects.filter(pk=open_order.pk).update(created_at=timezone.make_aware(datetime.combine(today, time(9))))
                self.product.stock = 3; self.product.save(update_fields=['stock'])
            for label, params in [('30', {'period': '30'}), ('7', {'period': '7'}),
                    ('custom', {'period': 'custom', 'date_from': '2026-10-15', 'date_to': '2026-10-19'}),
                    ('weekly', {'period': '30', 'grouping': 'weekly'}),
                    ('monthly', {'period': '30', 'grouping': 'monthly'}),
                    ('horizon', {'period': '30', 'forecast_horizon': '30'})]:
                with patch('django.utils.timezone.localdate', return_value=today):
                    page = self.analytics_page(**params)
                (target/f'{state}-{label}.html').write_bytes(page.content)
                (target/f'{state}-{label}.json').write_text(json.dumps(page.context['analytics'], default=str), encoding='utf-8')

    def sale(self, amount, stamp, **fields):
        return MarketplaceOrder.objects.create(product=self.product, product_name=self.product.name,
            quantity=fields.pop('quantity', 1), total_price=Decimal(amount),
            status=fields.pop('status', 'completed'), payment_status=fields.pop('payment_status', 'paid'),
            completed_at=stamp, **fields)

    def test_super_presets_ignore_stale_custom_dates_on_every_tab(self):
        from unittest.mock import patch
        with patch('django.utils.timezone.localdate', return_value=self.today):
            for module in ('marketplace', 'facilities', 'services', 'users'):
                for key, days in [('7', 7), ('30', 30), ('90', 90)]:
                    page = self.analytics_page(module, period=key, date_from='2026-01-01', date_to='2026-01-02')
                    self.assertEqual(page.context['analytics_period'].days, days)
                    self.assertEqual(page.context['analytics_period'].end, self.today)
                custom = self.analytics_page(module, period='custom', date_from='2026-09-30', date_to='2026-10-01')
                self.assertEqual(custom.context['analytics_period'].days, 2)
        invalid = self.client.get(reverse('admin_marketplace_analytics_page'),
            {'module': 'users', 'period': 'custom', 'date_from': '2026-10-02', 'date_to': '2026-10-01'})
        self.assertEqual(invalid.status_code, 400)

    def test_super_comparisons_reconcile_with_report_and_no_growth_from_zero(self):
        from modules.reports.reporting import build_report
        start, end = date(2026, 10, 1), date(2026, 10, 2)
        self.sale('40', timezone.make_aware(datetime(2026, 9, 29, 12)))
        self.sale('80', timezone.make_aware(datetime(2026, 10, 1, 12)), fulfillment_method='seller_delivery')
        self.sale('999', timezone.make_aware(datetime(2026, 10, 1, 12)), payment_status='unpaid')
        page = self.analytics_page(period='custom', date_from=str(start), date_to=str(end))
        data = page.context['analytics']
        self.assertEqual(data['comparison']['sales']['percentage_change'], 100)
        self.assertEqual(data['comparison']['orders']['percentage_change'], 0)
        self.assertEqual((data['comparison']['start'], data['comparison']['end']), (date(2026, 9, 29), date(2026, 9, 30)))
        report = build_report('sales', start, end, user=self.super_admin)
        self.assertEqual(sum(Decimal(row['Amount (PHP)']) for row in report['rows']), Decimal(data['kpis']['sales']))
        MarketplaceOrder.objects.filter(completed_at__date__lt=start).delete()
        data = self.analytics_page(period='custom', date_from=str(start), date_to=str(end)).context['analytics']
        self.assertIsNone(data['comparison']['sales']['percentage_change'])
        self.assertEqual(data['comparison']['sales']['trend_state'], 'new_activity')
        MarketplaceOrder.objects.all().delete()
        empty = self.analytics_page(period='custom', date_from=str(start), date_to=str(end)).context['analytics']
        self.assertIsNone(empty['comparison']['sales']['percentage_change'])
        self.assertEqual(empty['comparison']['sales']['direction'], 'unchanged')

    def test_super_midnight_revenue_zero_price_and_creation_date_drilldown(self):
        from urllib.parse import urlparse
        from datetime import timezone as dt_timezone
        self.sale('10', datetime(2026, 9, 30, 15, 59, tzinfo=dt_timezone.utc))
        inside = self.sale('0', datetime(2026, 9, 30, 16, 0, tzinfo=dt_timezone.utc))
        self.sale('20', datetime(2026, 10, 1, 15, 59, tzinfo=dt_timezone.utc))
        self.sale('999', datetime(2026, 10, 1, 16, 0, tzinfo=dt_timezone.utc))
        MarketplaceOrder.objects.filter(pk=inside.pk).update(created_at=timezone.make_aware(datetime(2026, 10, 1, 1)))
        page = self.analytics_page(period='custom', date_from='2026-10-01', date_to='2026-10-01')
        data = page.context['analytics']
        self.assertEqual((data['kpis']['sales'], data['kpis']['completed_orders']), ('20.00', 2))
        self.assertContains(page, 'marketplaceSalesChartDescription')
        row = next(row for row in data['order_status_breakdown']['rows'] if row['status'] == 'completed')
        detail = self.client.get(row['url'])
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.context['order_stats']['total'], row['count'])
        self.assertEqual(urlparse(row['url']).path, reverse('admin_orders_page'))

    def test_super_empty_and_zero_price_chart_states(self):
        page = self.analytics_page(period='30')
        self.assertNotContains(page, '<canvas id="marketplaceSalesChart"')
        self.assertContains(page, 'No Sales Data Yet')
        self.assertContains(page, 'No orders submitted in selected period.')
        self.assertNotContains(page, 'Monthly Sales Performance')
        self.assertNotContains(page, 'Cash-on-Pickup orders')
        self.sale('0', timezone.now())
        page = self.analytics_page(period='30')
        self.assertContains(page, '<canvas id="marketplaceSalesChart"')
        self.assertNotContains(page, 'No Sales Data Yet')
        self.assertNotContains(page, '<canvas id="marketplaceCategoryChart"')
        self.assertContains(page, 'Qualifying zero-price sales are retained in the data table.')
        self.assertNotContains(page, '<canvas id="peakSalesChart"')

    def test_super_user_month_clipping_unknown_types_and_query_bound(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from modules.reports.analytics_sections import build_users_tab_analytics
        from modules.marketplace.services.analytics import AnalyticsPeriod
        unknown = CampusHubUser.objects.create(username='unclassified-analytics', email='unclassified@example.test',
            password_hash='unused', user_type='legacy')
        CampusHubUser.objects.filter(pk=unknown.pk).update(created_at=timezone.make_aware(datetime(2026, 9, 30, 23, 59)))
        first = User.objects.create_user(username='month-edge-analytics', date_joined=timezone.make_aware(datetime(2026, 10, 1)))
        last = User.objects.create_user(username='month-outside-analytics', date_joined=timezone.make_aware(datetime(2026, 10, 2)))
        period = AnalyticsPeriod('custom', 'One day', date(2026, 10, 1), date(2026, 10, 1))
        with CaptureQueriesContext(connection) as queries:
            data = build_users_tab_analytics(period, {}, user=self.super_admin)
        self.assertEqual(data['main_chart']['labels'], ['Oct 2026'])
        self.assertEqual(sum(data['main_chart']['values']), data['kpis']['new_registrations'])
        self.assertEqual(sum(data['main_chart']['values']), 1)
        unknown_count = CampusHubUser.objects.exclude(user_type__in=[CampusHubUser.USER_TYPE_STUDENT,
            CampusHubUser.USER_TYPE_FACULTY, CampusHubUser.USER_TYPE_GUEST]).count()
        self.assertEqual(next(row['count'] for row in data['distribution'] if row['type_code']=='unclassified'), unknown_count)
        self.assertEqual(next(row['count'] for row in data['distribution'] if row['type_code']=='student'),
            CampusHubUser.objects.filter(user_type=CampusHubUser.USER_TYPE_STUDENT).count())
        self.assertEqual(sum(row['count'] for row in data['distribution']), data['kpis']['total_users'])
        self.assertEqual(next(row['role'] for row in data['distribution'] if row['type_code']=='admin'),
            'Web Accounts (recorded roles)')
        self.assertLessEqual(len(queries), 18)

    def test_super_facility_capacity_clips_hours_and_checkout_and_batches_queries(self):
        from uuid import uuid4
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from api.models import Room
        from modules.reports.superadmin_analytics import facility_capacity_rows
        from modules.marketplace.services.analytics import AnalyticsPeriod
        period = AnalyticsPeriod('custom', 'Two days', date(2026, 10, 1), date(2026, 10, 2))
        court = Facility.objects.create(id='verified-hours', facility_name='Verified court', facility_type='covered_court',
            workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        hostel = Facility.objects.create(id='verified-nights', facility_name='Verified hostel', facility_type='hostel')
        room = Room.objects.create(id=uuid4(), facility=hostel, room_name='A')
        Booking.objects.create(id='verified-court-order', facility=court, booking_date=period.start,
            start_time=time(7), end_time=time(11), status='approved')
        Booking.objects.create(id='verified-stay-order', facility=hostel, booking_date=None, room_id=room.id,
            check_in_date=date(2026, 9, 29), check_out_date=date(2026, 10, 2), status='completed')
        with CaptureQueriesContext(connection) as queries:
            data = facility_capacity_rows(period, [court, hostel, self.court])
        self.assertEqual(len(queries), 2)
        self.assertEqual((data[court.pk]['usage'], data[court.pk]['capacity'], data[court.pk]['utilization']), (3, 20, 15))
        self.assertEqual((data[hostel.pk]['usage'], data[hostel.pk]['capacity'], data[hostel.pk]['utilization']), (1, 2, 50))
        self.assertEqual(data[self.court.pk]['capacity_state'], 'unavailable')
        self.assertIsNone(data[self.court.pk]['utilization'])

    def test_super_facility_submission_trend_clips_month_and_preserves_booking_semantics(self):
        from modules.reports.analytics_sections import build_facility_tab_analytics
        from modules.marketplace.services.analytics import AnalyticsPeriod
        period = AnalyticsPeriod('custom', 'Two days', date(2026, 10, 1), date(2026, 10, 2))
        for index, stamp in enumerate([datetime(2026, 9, 30, 23), datetime(2026, 10, 1), datetime(2026, 10, 3)]):
            booking = Booking.objects.create(id='trend-clip-'+str(index), facility=self.court,
                booking_date=period.start, start_time=time(8), end_time=time(10), status='approved')
            Booking.objects.filter(pk=booking.pk).update(created_at=timezone.make_aware(stamp))
        data = build_facility_tab_analytics(period, {}, user=self.super_admin)
        self.assertEqual(data['kpis']['approved_bookings'], 3)
        self.assertEqual(data['monthly_trend'], {'labels':['Oct 2026'], 'values':[1]})

    def test_super_inventory_bundle_basis_algorithms_and_shared_role_isolation(self):
        from api.models import BundleComponent
        from modules.marketplace.services.analytics import build_marketplace_analytics
        from modules.reports.superadmin_analytics import enrich_marketplace
        bundle = Product.objects.create(seller=self.seller_user, name='Derived test bundle', product_type='bundle',
            price=10, approval_status='approved')
        BundleComponent.objects.create(bundle=bundle, product=self.product, required_quantity=2)
        data = build_marketplace_analytics({'period':'30'}, user=self.super_admin)
        original_forecast, original_baskets = data['forecast'].copy(), data['market_basket'].copy()
        enrich_marketplace(data, self.super_admin)
        self.assertEqual(data['forecast'], original_forecast)
        self.assertEqual(data['market_basket'], original_baskets)
        self.assertFalse(data['market_basket']['sufficient'])
        row = next(row for row in data['inventory']['all_rows'] if row['product_id']==bundle.pk)
        self.assertEqual(row['stock_basis'], 'Component-derived availability')
        self.assertEqual(row['stock'], 12)
        self.assertEqual(self.product.stock, 25)
        self.client.force_login(self.marketplace_admin)
        page = self.client.get(reverse('admin_marketplace_analytics_page'))
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'super-admin-analytics')
        self.assertContains(page, 'Monthly Sales Performance')
        self.assertNotIn('comparison', page.context['analytics'])

    def test_super_facility_revenue_alternative_preserves_shared_dashboard(self):
        from api.models import FacilityPayment
        from django.template.loader import render_to_string
        page = self.analytics_page('facilities', period='30')
        self.assertContains(page, 'data-revenue-table hidden')
        booking = Booking.objects.create(id='analytics-paid-facility', facility=self.court,
            booking_date=timezone.localdate(), status='approved')
        FacilityPayment.objects.create(id='analytics-paid-payment', booking=booking,
            payment_status='paid', paid_amount=Decimal('125.25'), paid_at=timezone.now())
        page = self.analytics_page('facilities', period='30')
        self.assertEqual(page.context['facility_analytics']['revenue_overview']['total'], '125.25')
        self.assertEqual(sum(Decimal(row[1]) for row in page.context['facility_revenue_table']['rows']), Decimal('125.25'))
        self.assertContains(page, 'Verified facility revenue by recognition date')
        legacy = render_to_string('dashboard/partials/facility_revenue.html', {'facility_analytics':page.context['facility_analytics']})
        self.assertNotIn('data-revenue-table', legacy)
        self.client.force_login(self.facilities_admin)
        shared = self.client.get(reverse('admin_facility_analytics_page'), {'period':'30'})
        self.assertEqual(shared.status_code, 200)
        self.assertNotContains(shared, 'super-admin-analytics')
        self.assertNotContains(shared, 'data-revenue-table')

    def test_optional_super_analytics_browser_fixtures(self):
        import os, json
        from pathlib import Path
        destination = os.environ.get('SUPER_ANALYTICS_REVIEW_DIR')
        if not destination:
            return
        target = Path(destination); target.mkdir(parents=True, exist_ok=True)
        old = timezone.now() - timedelta(days=90)
        User.objects.all().update(date_joined=old)
        CampusHubUser.objects.all().update(created_at=old)
        for state in ('empty','populated'):
            if state == 'populated':
                SellerRequest.objects.create(user=self.seller_user, student_id='fixture-seller', status='approved')
                for offset in range(3):
                    self.sale('1350', timezone.now()-timedelta(days=offset), quantity=3,
                        fulfillment_method='seller_delivery', buyer_user_id=self.ch_user.pk)
                other = Product.objects.create(seller=self.seller_user, name='Recorded second product', price=25,
                    stock=4, category='Food', approval_status='approved')
                MarketplaceOrder.objects.create(product=other, product_name=other.name, quantity=1,
                    total_price=25, status='completed', payment_status='paid', completed_at=timezone.now())
                User.objects.create_user(username='fixture-new-account', date_joined=timezone.now())
                self.court.facility_type='covered_court'
                self.court.workflow_config={'operating_hours':'Daily 08:00-18:00'}
                self.court.save(update_fields=['facility_type','workflow_config'])
                booking = Booking.objects.create(id='fixture-facility', facility=self.court, booking_date=timezone.localdate(),
                    start_time=time(8), end_time=time(10), status='approved')
                from api.models import FacilityPayment
                FacilityPayment.objects.create(id='fixture-paid-facility', booking=booking,
                    payment_status='paid', paid_amount=Decimal('125.25'), paid_at=timezone.now())
                Booking.objects.create(id='fixture-service', facility=self.lab, booking_date=timezone.localdate(), status='completed')
            for module in ('marketplace','facilities','services','users'):
                page = self.analytics_page(module, period='30')
                (target/(state+'-'+module+'.html')).write_bytes(page.content)
                if module=='marketplace':
                    (target/(state+'-marketplace.json')).write_text(json.dumps(page.context['analytics'], default=str), encoding='utf-8')
        # Verify a real zero-price cohort and weekly/monthly grouping without replacing the renderer.
        MarketplaceOrder.objects.all().delete()
        self.sale('0', timezone.now())
        page = self.analytics_page(period='30')
        (target/'zero-marketplace.html').write_bytes(page.content)
        for grouping in ('weekly','monthly'):
            page = self.analytics_page(period='30', grouping=grouping)
            (target/(grouping+'-marketplace.html')).write_bytes(page.content)
        # Compare existing shared-role HTML against the exact pre-change template.
        from django.template import engines
        import re
        for actor, module, template in [(self.marketplace_admin, 'marketplace', 'marketplace'),
                                        (self.facilities_admin, 'facilities', 'facility')]:
            self.client.force_login(actor)
            page = self.client.get(reverse('admin_marketplace_analytics_page'), {'module':module, 'period':'30'})
            self.assertEqual(page.status_code, 200)
            (target/('shared-'+module+'.html')).write_bytes(page.content)
            old_path = target.parent / 'before/backend/core/modules/reports/templates/reports/pages' / ('admin_'+template+'_analytics.html')
            if old_path.exists():
                context = {}
                for layer in page.context:
                    context.update(layer.flatten())
                old = engines['django'].from_string(old_path.read_text(encoding='utf-8')).render(context, request=page.wsgi_request)
                normalize = lambda text: re.sub(r'\s+', ' ', re.sub(r'(?<=>)\s+(?=<)', '', text)).strip()
                self.assertEqual(normalize(old), normalize(page.content.decode()))
