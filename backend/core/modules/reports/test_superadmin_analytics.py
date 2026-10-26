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
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
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
        from .reporting import build_report
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
        from .analytics_sections import build_users_tab_analytics
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
        from .superadmin_analytics import facility_capacity_rows
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
        from .analytics_sections import build_facility_tab_analytics
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
        from .superadmin_analytics import enrich_marketplace
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
