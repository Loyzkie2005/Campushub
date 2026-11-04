"""Shared-account populations, seller-source identities and AOV through authorized pages/APIs."""
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from accounts import tests as fixtures
from accounts.models import User
from api.models import CampusHubUser, MarketplaceOrder, Product, SellerRequest
from .account_metrics import account_population
from .dashboard_periods import build_dashboard_data
from .analytics_sections import build_users_tab_analytics
from modules.marketplace.services.analytics import build_marketplace_analytics
from .superadmin_analytics import enrich_marketplace


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DashboardMarketplaceParityTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 11, 2)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        MarketplaceOrder.objects.all().delete()
        SellerRequest.objects.all().delete()
        User.objects.all().update(date_joined=self.stamp(self.today - timedelta(days=100)))
        CampusHubUser.objects.all().update(created_at=self.stamp(self.today - timedelta(days=100)))
        self.client.force_login(self.super_admin)

    def stamp(self, day):
        return timezone.make_aware(datetime.combine(day, time(12)))

    def projections(self, period='last_30_days'):
        dashboard = build_dashboard_data({'period': period}, today=self.today)
        dates = dashboard['period']
        analytics = build_marketplace_analytics({'period': 'custom', 'date_from': dates['start_date'], 'date_to': dates['end_date']}, today=self.today, user=self.super_admin, refined=True)
        enrich_marketplace(analytics, self.super_admin)
        return dashboard, analytics

    def test_web_mobile_population_matches_users_analytics_and_registration_counts(self):
        User.objects.filter(pk=self.super_admin.pk).update(date_joined=self.stamp(self.today))
        CampusHubUser.objects.filter(pk=self.ch_user.pk).update(created_at=self.stamp(self.today), is_suspended=True)
        self.super_admin.is_suspended = True; self.super_admin.save(update_fields=['is_suspended'])
        dashboard, analytics = self.projections()
        users = build_users_tab_analytics(analytics['period'], {}, user=self.super_admin)
        self.assertEqual(dashboard['kpis']['total_users']['value'], User.objects.count() + CampusHubUser.objects.count())
        self.assertEqual(dashboard['kpis']['total_users']['new_in_period'], 2)
        self.assertEqual(users['kpis']['total_users'], dashboard['kpis']['total_users']['value'])
        self.assertEqual(users['kpis']['new_registrations'], 2)
        self.assertEqual(dashboard['executive']['users']['new_registrations'], 2)
        population = account_population(analytics['period'])
        self.assertEqual(users['kpis']['active_users'], sum(row['active'] for row in population.values()))
        self.assertLess(users['kpis']['active_users'], users['kpis']['total_users'])

    def test_mobile_seller_access_includes_idle_sellers_and_separates_source_ids(self):
        # Fixture deliberately has equal numeric web/mobile IDs; they are distinct accounts.
        self.assertEqual(self.seller.pk, self.ch_user.pk)
        SellerRequest.objects.create(user=self.seller, student_id='web-parity', status='approved', reviewed_at=self.stamp(self.today))
        SellerRequest.objects.create(mobile_user=self.ch_user, student_id='mobile-parity', status='approved', reviewed_at=self.stamp(self.today))
        Product.objects.all().update(updated_at=self.stamp(self.today - timedelta(days=100)), submitted_at=self.stamp(self.today - timedelta(days=100)))
        dashboard, analytics = self.projections()
        self.assertEqual(dashboard['kpis']['active_sellers']['value'], 2)
        self.assertEqual(dashboard['kpis']['active_sellers']['approved_in_period'], 2)
        self.assertEqual(analytics['kpis']['active_sellers'], 0)
        self.ch_user.is_suspended = True; self.ch_user.save(update_fields=['is_suspended'])
        dashboard, _ = self.projections()
        self.assertEqual(dashboard['kpis']['active_sellers']['value'], 1)

    def test_undefined_aov_differs_from_real_zero_price_sales_in_ssr_and_refresh(self):
        for index in range(3):
            order = MarketplaceOrder.objects.create(product=self.prod_low, product_name=self.prod_low.name, quantity=1,
                total_price=50, status='pending', payment_status='unpaid')
            MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=self.stamp(self.today))
        with patch('django.utils.timezone.localdate', return_value=self.today):
            page = self.client.get(reverse('admin_dashboard_page'), {'period': 'last_30_days'})
            payload = self.client.get(reverse('admin_dashboard_api'), {'period': 'last_30_days'}).json()
        self.assertContains(page, 'data-metric="average"')
        self.assertContains(page, '>N/A</strong>')
        self.assertIsNone(payload['marketplace']['average_order_value'])
        average = next(row for row in payload['marketplace']['sales_overview']['metrics'] if row['key'] == 'average')
        self.assertEqual((average['value'], average['currency']), ('N/A', False))
        self.assertEqual(payload['kpis']['total_orders']['value'], 3)
        self.assertEqual(payload['kpis']['marketplace_revenue']['value'], 0)
        dashboard, analytics = self.projections()
        self.assertIsNone(analytics['kpis']['average_order_value'])
        self.assertIsNone(analytics['revenue_aov']['current'])
        free = MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
            quantity=1, total_price=0, status='completed', payment_status='paid', completed_at=self.stamp(self.today))
        MarketplaceOrder.objects.filter(pk=free.pk).update(created_at=self.stamp(self.today))
        dashboard, analytics = self.projections()
        self.assertEqual(dashboard['marketplace']['average_order_value'], 0)
        self.assertEqual(analytics['revenue_aov']['current'], '0.00')
        self.assertEqual(next(m for m in dashboard['marketplace']['sales_overview']['metrics'] if m['key'] == 'average')['value'], '0.00')

    def test_dashboard_links_preserve_dates_and_choose_each_protected_tab(self):
        dashboard, _ = self.projections()
        with patch('django.utils.timezone.localdate', return_value=self.today):
            for module, url in dashboard['executive']['analytics_urls'].items():
                response = self.client.get(url)
                self.assertContains(response, f'data-analytics-module="{module}"')
                self.assertEqual(response.context['analytics_period'].start.isoformat(), dashboard['period']['start_date'])
                self.assertEqual(response.context['analytics_period'].end.isoformat(), dashboard['period']['end_date'])
        self.client.force_login(self.facilities_admin)
        self.assertEqual(self.client.get(reverse('admin_dashboard_api')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin_marketplace_analytics_page')).status_code, 403)

    @override_settings(TIME_ZONE='Asia/Manila')
    def test_philippine_midnight_cohorts_match_across_both_pages(self):
        inside = datetime(2026, 11, 1, 16, 30, tzinfo=dt_timezone.utc)  # Nov 2, 00:30 locally.
        outside = datetime(2026, 11, 1, 15, 30, tzinfo=dt_timezone.utc)  # Nov 1, 23:30 locally.
        for stamp, status, payment, amount in [(inside, 'completed', 'paid', 100), (inside, 'pending', 'unpaid', 50), (outside, 'pending', 'unpaid', 75)]:
            order = MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                quantity=1, total_price=amount, status=status, payment_status=payment,
                completed_at=stamp if status == 'completed' else None)
            MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=stamp)
        User.objects.filter(pk=self.super_admin.pk).update(date_joined=inside)
        CampusHubUser.objects.filter(pk=self.ch_user.pk).update(created_at=outside)
        dashboard, analytics = self.projections('today')
        self.assertEqual(dashboard['kpis']['total_orders']['value'], analytics['operations']['total'])
        self.assertEqual(analytics['operations']['total'], 2)
        self.assertEqual(analytics['submission_comparison']['rows'][0]['previous'], 1)
        self.assertEqual(dashboard['kpis']['marketplace_revenue']['value'], 100)
        self.assertEqual(analytics['kpis']['sales'], '100.00')
        self.assertEqual(dashboard['kpis']['total_users']['new_in_period'], 1)
        self.assertEqual(build_users_tab_analytics(analytics['period'], {}, user=self.super_admin)['kpis']['new_registrations'], 1)
