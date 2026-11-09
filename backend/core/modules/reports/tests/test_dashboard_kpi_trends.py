# Original location: backend/core/modules/reports/test_dashboard_kpi_trends.py
"""Real database activity comparisons; fixtures never enter working data."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import re
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from api.models import Booking, CampusHubUser, Facility, MarketplaceOrder, Product
from modules.marketplace.services.analytics import AnalyticsPeriod
from modules.reports.dashboard_kpi_trends import activity_trend, comparison_dates, attach_kpi_trends
from modules.reports.dashboard_periods import resolve_dashboard_period


class KPITrendMathTests(SimpleTestCase):
    def test_percentage_direction_zero_and_small_decimal_changes(self):
        period = AnalyticsPeriod('custom', 'Custom Range', date(2026, 3, 1), date(2026, 3, 31))
        cases = [(150, 100, '+50%', 'up', 50), (50, 100, '−50%', 'down', -50),
                 (100, 100, '', 'neutral', 0), (0, 100, '−100%', 'down', -100),
                 (100, 0, '↗ New Activity', 'up', None), (0, 0, '', 'neutral', None),
                 ('100.01', 100, '+<0.1%', 'up', .01), (100, '100.01', '−<0.1%', 'down', -.01),
                 ('108.53', 100, '+8.5%', 'up', 8.53), ('100.0001', 100, '', 'neutral', 0)]
        for current, previous, label, direction, percentage in cases:
            with self.subTest(current=current, previous=previous):
                trend = activity_trend(current, previous, period, basis='Recorded activity', context='Existing explanation')
                self.assertEqual((trend['label'], trend['direction'], trend['percentage_change']), (label, direction, percentage))
                self.assertIn('Existing explanation', trend['explanation'])
                self.assertEqual(trend['visible'], bool(label))

    def test_every_existing_preset_compares_equal_nonoverlapping_local_days(self):
        for today in (date(2026, 3, 31), date(2024, 2, 29), date(2026, 1, 1)):
            for key in ('today', 'last_7_days', 'last_30_days', 'last_90_days', 'this_month', 'previous_month', 'this_year', 'custom'):
                with self.subTest(today=today, key=key):
                    period, _ = resolve_dashboard_period({'period': key, 'start_date': '2023-12-29', 'end_date': '2024-01-01'}, today)
                    start, end = comparison_dates(period)
                    self.assertEqual((end - start).days + 1, period.days)
                    self.assertEqual(end + timedelta(days=1), period.start)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class KPITrendDatabaseTests(TestCase):
    today = date(2026, 3, 31)
    trend_keys = {'total_users', 'total_orders', 'total_bookings', 'marketplace_revenue'}

    def setUp(self):
        self.root = User.objects.create_superuser(username='trend-root', password='test')
        User.objects.filter(pk=self.root.pk).update(date_joined=self.stamp(date(2020, 1, 1)))
        self.client.force_login(self.root)
        self.product = Product.objects.create(seller=self.root, name='Isolated trend fixture', category='Supplies', price=10, stock=0)
        self.court = Facility.objects.create(id='TREND-COURT', facility_name='Fixture court', facility_type='covered_court')
        self.lab = Facility.objects.create(id='TREND-LAB', facility_name='Fixture lab', facility_type='food_analysis', booking_mode='service')

    def stamp(self, day, at=time(12)):
        with timezone.override('Asia/Manila'):
            return timezone.make_aware(datetime.combine(day, at))

    def order(self, day, amount='100', status='completed', payment='paid', submitted=None):
        row = MarketplaceOrder.objects.create(product=self.product, product_name=self.product.name, quantity=1,
            unit_price=amount, total_price=amount, status=status, payment_status=payment,
            completed_at=self.stamp(day), paid_at=self.stamp(day))
        MarketplaceOrder.objects.filter(pk=row.pk).update(created_at=submitted or self.stamp(day))
        return row

    def booking(self, identifier, day, *, service=False):
        row = Booking.objects.create(id=identifier, facility=self.lab if service else self.court,
            booking_date=date(2027, 1, 1), start_time=time(9), end_time=time(10), status='cancelled')
        Booking.objects.filter(pk=row.pk).update(created_at=self.stamp(day))
        return row

    def registration(self, username, day, *, mobile=False):
        if mobile:
            row = CampusHubUser.objects.create(username=username, email=username+'@example.test', password_hash='unused', user_type='student')
            CampusHubUser.objects.filter(pk=row.pk).update(created_at=self.stamp(day))
        else:
            row = User.objects.create_user(username=username, date_joined=self.stamp(day))
        return row

    def response(self, *, page=False, params=None):
        with patch('django.utils.timezone.localdate', return_value=self.today):
            response = self.client.get(reverse('admin_dashboard_page' if page else 'admin_dashboard_api'), params or {'period': 'today'})
        self.assertEqual(response.status_code, 200, response.content[:500])
        return response

    def capture(self, name):
        directory = os.environ.get('KPI_TREND_REVIEW_DIR')
        if directory:
            folder = Path(directory)
            folder.mkdir(parents=True, exist_ok=True)
            (folder / (name+'.html')).write_bytes(self.response(page=True).content)
            (folder / (name+'.json')).write_text(json.dumps(self.response().json()), encoding='utf-8')

    def test_four_real_trends_lifetime_total_and_submission_revenue_populations(self):
        prior = self.today - timedelta(days=1)
        self.registration('current-web', self.today)
        self.registration('current-mobile', self.today, mobile=True)
        disabled = self.registration('current-disabled', self.today)
        User.objects.filter(pk=disabled.pk).update(is_active=False)
        self.registration('previous-web', prior)
        self.order(self.today, '120')
        self.order(self.today, '80')
        for status, payment in [('pending', 'paid'), ('cancelled', 'paid'), ('completed', 'unpaid')]:
            self.order(self.today, '9000', status, payment)
        self.order(prior)
        self.order(prior, '9000', 'completed', 'unpaid')
        for i in range(2):
            self.booking('current-'+str(i), self.today)
        for i in range(4):
            self.booking('prior-'+str(i), prior)
        self.booking('excluded-service', self.today, service=True)
        kpis = self.response().json()['kpis']
        self.assertEqual(kpis['total_users']['value'], 5)
        expected = {'total_users': (3, 1, 200), 'total_orders': (5, 2, 150),
                    'total_bookings': (2, 4, -50), 'marketplace_revenue': (200, 100, 100)}
        self.assertEqual({key for key, metric in kpis.items() if 'trend' in metric}, self.trend_keys)
        for key, values in expected.items():
            trend = kpis[key]['trend']
            self.assertEqual((trend['current_value'], trend['previous_value'], trend['percentage_change']), values)
        self.assertIn('3 new in selected period', kpis['total_users']['secondary_text'])
        self.assertNotIn('success', kpis['total_orders']['trend']['label'])
        html = self.response(page=True).content.decode()
        self.assertEqual(set(re.findall(r'data-dashboard-trend="([^"]+)"', html)), self.trend_keys)
        self.assertEqual(len(re.findall('data-dashboard-kpi=', html)), 8)
        self.assertEqual(html.count('class="dashboard-kpi-value-row"'), 4)
        self.assertNotIn('dashboard-kpi-trend__badge', html)
        self.assertNotIn('data-trend-arrow', html)
        self.assertEqual(len(re.findall(r'data-dashboard-secondary="[^"]+"[^>]*>vs\. previous period</small>', html)), 4)
        self.assertIn('All web and mobile accounts', html)
        self.capture('mixed')

    def test_zero_activity_and_new_activity_keep_undefined_percentages_neutral(self):
        kpis = self.response().json()['kpis']
        for key in self.trend_keys:
            self.assertEqual((kpis[key]['trend']['label'], kpis[key]['trend']['percentage_change'], kpis[key]['trend']['visible']), ('', None, False))
        self.capture('empty')
        self.order(self.today, '50')
        self.registration('new-web', self.today)
        self.booking('new-booking', self.today)
        for key in self.trend_keys:
            trend = self.response().json()['kpis'][key]['trend']
            self.assertEqual((trend['label'], trend['direction'], trend['percentage_change'], trend['visible']), ('↗ New Activity', 'up', None, True))
        self.capture('new')

    def test_zero_current_with_prior_activity_displays_negative_one_hundred(self):
        prior = self.today - timedelta(days=1)
        self.order(prior)
        self.registration('old-web', prior)
        self.booking('old-booking', prior)
        for key in self.trend_keys:
            trend = self.response().json()['kpis'][key]['trend']
            self.assertEqual((trend['label'], trend['direction'], trend['percentage_change']), ('−100%', 'down', -100))
        self.capture('decline')

    def test_equal_nonzero_activity_hides_trends_and_captions_without_na(self):
        prior = self.today - timedelta(days=1)
        for day in (prior, self.today):
            self.order(day)
            self.registration('equal-'+str(day), day)
            self.booking('equal-'+str(day), day)
        for key in self.trend_keys:
            trend = self.response().json()['kpis'][key]['trend']
            self.assertEqual((trend['percentage_change'], trend['visible'], trend['label']), (0, False, ''))
        html = self.response(page=True).content.decode()
        section = html.split('aria-labelledby="systemOverviewTitle"', 1)[1].split('</section>', 1)[0]
        self.assertNotIn('N/A', section)
        self.assertNotIn('>vs. previous period<', section)
        self.assertEqual(len(re.findall(r'data-dashboard-trend="[^"]+"[^>]* hidden', section)), 4)
        self.capture('steady')

    def test_month_end_uses_equal_kpi_days_without_changing_other_comparisons(self):
        self.order(date(2026, 2, 1), '100')  # Legacy calendar comparison.
        self.order(date(2026, 1, 29), '100')  # Within the preceding 31 days.
        self.order(date(2026, 3, 31), '300')
        payload = self.response(params={'period': 'this_month'}).json()
        trend = payload['kpis']['marketplace_revenue']['trend']
        self.assertEqual((trend['previous_start_date'], trend['previous_end_date'], trend['days']), ('2026-01-29', '2026-02-28', 31))
        self.assertEqual((trend['previous_value'], trend['percentage_change']), (200, 50))
        self.assertEqual(payload['period']['previous_start_date'], '2026-02-01')
        self.assertEqual(payload['kpis']['marketplace_revenue']['previous_value'], 100)

    @override_settings(TIME_ZONE='UTC')
    def test_manila_midnight_and_completion_dates_define_activity(self):
        start = self.stamp(self.today, time.min)
        old_submission = self.stamp(date(2020, 1, 1))
        current = self.order(self.today, '50', submitted=old_submission)
        previous = self.order(self.today, '25', submitted=old_submission)
        MarketplaceOrder.objects.filter(pk=current.pk).update(completed_at=start)
        MarketplaceOrder.objects.filter(pk=previous.pk).update(completed_at=start-timedelta(microseconds=1))
        web = self.registration('midnight', self.today)
        User.objects.filter(pk=web.pk).update(date_joined=start)
        old = self.registration('before-midnight', self.today, mobile=True)
        CampusHubUser.objects.filter(pk=old.pk).update(created_at=start-timedelta(microseconds=1))
        payload = self.response().json()['kpis']
        self.assertEqual(payload['total_users']['trend']['percentage_change'], 0)
        self.assertEqual(payload['marketplace_revenue']['trend']['percentage_change'], 100)
        self.assertEqual(payload['total_orders']['trend']['current_value'], 0)
        self.assertEqual(payload['marketplace_revenue']['trend']['timezone'], 'Asia/Manila')

    def test_trends_reuse_aggregates_without_queries_and_permissions_are_unchanged(self):
        period = AnalyticsPeriod('today', 'Today', self.today, self.today)
        kpis = {key: {'value': 0, 'secondary_text': 'Recorded context'} for key in self.trend_keys}
        with timezone.override('Asia/Manila'), self.assertNumQueries(0):
            attach_kpi_trends(kpis, period, new_users=0, previous_users=0, previous_bookings=0, previous_orders=0, current_sales=Decimal('0'), previous_sales=Decimal('0'))
        self.client.logout()
        response = self.client.get(reverse('admin_dashboard_api'))
        self.assertIn(response.status_code, (302, 401, 403))
