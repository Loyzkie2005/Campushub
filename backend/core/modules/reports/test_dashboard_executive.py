"""Real-source executive summaries, domain boundaries and Analytics destinations."""
from datetime import date, datetime, time
from unittest.mock import patch
import json
import os
from pathlib import Path
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from accounts import tests as fixtures
from accounts.models import AccountActivity
from api.models import Booking, Facility, FacilityPayment


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ExecutiveDashboardTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        Booking.objects.all().delete()
        self.client.force_login(self.super_admin)
        self.service = Facility.objects.create(id='EX-SERVICE', facility_name='Actual laboratory',
            facility_type='food_analysis', booking_mode='service')

    def request_record(self, key, status, *, service=True, day=None):
        row = Booking.objects.create(id=key, facility=self.service if service else self.fac_court,
            user=self.ch_user, status=status, total_amount=100, booking_date=date(2026, 10, 20),
            start_time=time(9), end_time=time(11))
        stamp = timezone.make_aware(datetime.combine(day or self.today, time(12)))
        Booking.objects.filter(pk=row.pk).update(created_at=stamp)
        return row

    def payload(self):
        with patch('django.utils.timezone.localdate', return_value=self.today):
            result = self.client.get(reverse('admin_dashboard_api'), {'period': 'today'})
        self.assertEqual(result.status_code, 200)
        return result.json()

    def test_services_period_counts_current_queue_and_physical_isolation(self):
        for key, status in [('S-P', Booking.STATUS_PENDING), ('S-A', Booking.STATUS_APPROVED),
                            ('S-C', Booking.STATUS_COMPLETED), ('S-X', Booking.STATUS_CANCELLED)]:
            self.request_record(key, status)
        self.request_record('S-OLD', Booking.STATUS_PENDING, day=date(2026, 9, 1))
        court = self.request_record('COURT-A', Booking.STATUS_APPROVED, service=False)
        Booking.objects.filter(pk=court.pk).update(booking_date=self.today)
        data = self.payload(); services = data['executive']['services']
        self.assertEqual({key: services[key] for key in ('active_services', 'open_requests', 'pending_requests', 'completed_requests', 'pending_current')},
                         dict(active_services=1, open_requests=2, pending_requests=1, completed_requests=1, pending_current=2))
        self.assertEqual(services['most_requested'], {'name': self.service.facility_name, 'count': 2})
        self.assertEqual(len(services['recent_requests']), 4)
        self.assertEqual({row['id'] for row in services['pending_queue']}, {'S-P', 'S-OLD'})
        self.assertEqual(data['executive']['booking_overview']['total'], 1)
        self.assertEqual(data['kpis']['total_bookings']['value'], 1)
        self.assertEqual(data['facilities']['booking_overview'], data['executive']['booking_overview'])
        self.assertEqual(data['kpis']['pending_approvals']['services'], 2)
        self.assertEqual([row['name'] for row in data['facilities']['most_booked_facilities']], [self.fac_court.facility_name])
        self.assertTrue(all(row['facility'] != self.service.facility_name for row in data['facilities']['upcoming_reservations']))
        self.assertEqual(data['attention_required']['pending_services'], 2)
        self.assertEqual(data['attention_required']['pending_bookings'], 0)
        service_alert = next(row for row in data['attention_required']['items'] if row['key'] == 'pending_services')
        self.assertEqual(service_alert['url'], reverse('admin_service_requests_page') + '?status=pending')

    def test_reserved_confirmed_reuses_recorded_payment_definition(self):
        settled = self.request_record('COURT-PAID', Booking.STATUS_APPROVED, service=False)
        partial = self.request_record('COURT-PART', Booking.STATUS_APPROVED, service=False)
        self.request_record('COURT-END', Booking.STATUS_COMPLETED, service=False)
        for key, row, amount in [('E-P1', settled, 60), ('E-P2', settled, 40), ('E-P3', partial, 50)]:
            FacilityPayment.objects.create(id=key, booking=row, paid_amount=amount, payment_status=FacilityPayment.PAYMENT_PAID)
        data = self.payload()['executive']['booking_overview']
        self.assertEqual((data['total'], data['approved'], data['reserved_confirmed'], data['completed']), (3, 2, 1, 1))

    def test_facilities_attention_is_current_physical_and_excludes_archived_services(self):
        Facility.objects.exclude(pk=self.service.pk).update(availability_status=Facility.STATUS_AVAILABLE)
        self.fac_court.availability_status = Facility.STATUS_MAINTENANCE
        self.fac_court.save(update_fields=['availability_status'])
        Facility.objects.filter(pk=self.service.pk).update(availability_status=Facility.STATUS_MAINTENANCE)
        for key, kind, mode in (('ASSESSMENT', 'other', 'assessment'), ('LEASE', 'lease_space', 'lease'),
                                ('TRAINING', 'training_kitchen', 'slot')):
            service = Facility.objects.create(id='ATT-'+key, facility_name=key, facility_type=kind,
                booking_mode=mode, availability_status=Facility.STATUS_UNAVAILABLE)
            Booking.objects.create(id='ATT-REQUEST-'+key, facility=service, status=Booking.STATUS_PENDING)
        Facility.objects.create(id='ATT-ARCHIVED', facility_name='Archived venue', is_archived=True,
            availability_status=Facility.STATUS_MAINTENANCE)
        Facility.objects.create(id='ATT-CLOSED', facility_name='Temporarily closed hall',
            availability_status=Facility.STATUS_UNAVAILABLE, booking_mode='slot')
        self.request_record('ATT-OLD', Booking.STATUS_PENDING, service=False, day=date(2026, 9, 1))
        self.request_record('ATT-SERVICE', Booking.STATUS_PENDING)
        self.request_record('ATT-APPROVED', Booking.STATUS_APPROVED, service=False)
        Booking.objects.create(id='ATT-SCHEDULE', facility=self.fac_court, status=Booking.STATUS_PENDING,
            purpose='[class] Existing academic schedule')
        data = self.payload()
        self.assertEqual(data['executive']['facility_attention'], {'pending': 1, 'maintenance': 1, 'unavailable': 1})
        self.assertEqual(data['executive']['booking_overview']['pending'], 0)
        self.assertEqual(data['executive']['booking_overview']['approved'], 1)
        self.assertEqual(data['executive']['booking_overview']['total'], 1)

    def test_facilities_layout_summary_charts_and_booking_links(self):
        directory = os.environ.get('FACILITIES_REVIEW_DIR')
        for state in ('empty', 'populated'):
            if state == 'populated':
                for index, status in enumerate((Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED, Booking.STATUS_PENDING)):
                    row = self.request_record('UI-FAC-'+str(index), status, service=False)
                    Booking.objects.filter(pk=row.pk).update(booking_date=date(2099, 1, 1) if index == 0 else self.today)
                extra = Facility.objects.create(id='UI-FAC-LONG', facility_name='University Function Hall and Institutional Events Center', booking_mode='slot')
                row = self.request_record('UI-FAC-LONG', Booking.STATUS_COMPLETED, service=False)
                Booking.objects.filter(pk=row.pk).update(facility=extra, booking_date=self.today)
                self.request_record('UI-OLD', Booking.STATUS_PENDING, service=False, day=date(2026, 9, 1))
            with patch('django.utils.timezone.localdate', return_value=self.today):
                page = self.client.get(reverse('admin_dashboard_page'), {'period': 'today'})
            self.assertEqual(page.status_code, 200)
            html = page.content.decode()
            section = html[html.index('<section class="executive-section executive-facilities"'):html.index('aria-labelledby="servicesOverviewTitle"')]
            for text in ('Monitor facility bookings, demand, and availability.', 'View Analytics',
                         'Booking Summary', 'Bookings in Selected Period', 'Approved Bookings', 'Pending Bookings',
                         'Booking Trend', 'Most-Booked Facilities', 'Facility Attention', 'facilities-reservations-table'):
                self.assertIn(text, section)
            self.assertNotIn('Booking Revenue', section)
            self.assertEqual(section.count('data-booking-overview'), 1)
            self.assertIn('id="facilityBookingOverviewChart"', section)
            self.assertIn('data-facility-ranking-chart tabindex=', section)
            self.assertIn('Top 5 by approved/completed bookings scheduled', section)
            data = self.payload()
            for row in data['facilities']['upcoming_reservations']:
                self.assertEqual(row['url'], reverse('admin_booking_details_page', kwargs={'booking_id': row['id']}))
                self.assertIn(row['url'], section)
                self.assertEqual(self.client.get(row['url']).status_code, 200)
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                (target / f'facilities-{state}.html').write_bytes(page.content)
                (target / f'facilities-{state}.json').write_text(json.dumps(data), encoding='utf-8')
                if state == 'populated':
                    analytics = self.client.get(reverse('admin_facility_analytics_page'), {'period': 'today'})
                    self.assertContains(analytics, 'Most Frequently Booked Facility')
                    self.assertNotContains(analytics, 'executive-facilities')
                    self.assertContains(analytics, 'Monthly Booking Trend')
                    (target / 'facilities-analytics.html').write_bytes(analytics.content)

    def test_recorded_activity_is_bounded_and_does_not_expose_connection_data(self):
        event = AccountActivity.objects.create(account_source='admin', account_id=self.super_admin.pk,
            activity_type='service_created', activity='Created service', module='Services', result='success',
            metadata={'actor_admin_id': self.super_admin.pk}, ip_address='192.0.2.3', user_agent='Private test agent')
        AccountActivity.objects.filter(pk=event.pk).update(created_at=timezone.make_aware(datetime.combine(self.today, time(12))))
        data = self.payload()['executive']['activities']
        self.assertLessEqual(len(data), 5)
        self.assertEqual(data[0]['module'], 'Services')
        self.assertEqual(data[0]['user'], self.super_admin.get_full_name() or self.super_admin.username)
        self.assertNotIn('192.0.2.3', json.dumps(data))
        self.assertNotIn('user_agent', json.dumps(data))

    def test_eight_sections_detailed_cards_only_in_analytics_and_export_fixture(self):
        self.request_record('SERVICE-P', Booking.STATUS_PENDING)
        with patch('django.utils.timezone.localdate', return_value=self.today):
            page = self.client.get(reverse('admin_dashboard_page'), {'period': 'today'})
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        anchors = ['systemOverviewTitle', 'dashboardAttentionTitle', 'marketplaceRecommendationsTitle',
                       'marketplaceOverviewTitle', 'facilitiesOverviewTitle', 'servicesOverviewTitle', 'usersOverviewTitle', 'recentActivitiesTitle']
        self.assertEqual([html.index('id="'+key+'"') for key in anchors], sorted(html.index('id="'+key+'"') for key in anchors))
        self.assertContains(page, 'id="marketplaceRecommendationsTitle"', count=1)
        for anchor in ('frequentlyBoughtTogether', 'crossSellSuggestions', 'bundleSuggestions', 'recommendationActivity'):
            self.assertNotContains(page, 'id="'+anchor+'"')
        self.assertLess(html.index('id="dashboardAttentionTitle"'), html.index('id="marketplaceRecommendationsTitle"'))
        self.assertContains(page, 'id="dashboardAttentionTitle"', count=1)
        self.assertNotContains(page, 'data-inline-system-status')
        self.assertNotContains(page, 'id="dashboardSystemStatus"')
        self.assertNotContains(page, 'id="systemStatusRetry"')
        self.assertContains(page, 'id="lowStockSlot"', count=1)
        self.assertLess(html.index('id="topSellingProductsCard"'), html.index('id="lowStockSlot"'))
        self.assertLess(html.index('id="recentOrdersSlot"'), html.index('id="lowStockSlot"'))
        for removed in ('categorySalesCard', 'facilityUtilizationCard', 'facilityRevenueCard', 'facilityOperationalStatusCard', 'accountsOverviewTitle', 'salesSampleData'):
            self.assertNotContains(page, 'id="'+removed+'"')
        for module in ('marketplace', 'facilities', 'services', 'users'):
            url = self.payload()['executive']['analytics_urls'][module]
            self.assertEqual(self.client.get(url).status_code, 200, module)
        analytics = self.client.get(reverse('admin_facility_analytics_page'), {'period': 'today'})
        self.assertContains(analytics, 'data-facility-revenue', count=1)
        self.assertContains(analytics, 'data-facility-operational-status', count=1)
        self.assertContains(analytics, 'data-facility-utilization', count=1)
        directory = os.environ.get('EXECUTIVE_REVIEW_DIR')
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            (target/'dashboard.html').write_bytes(page.content)
            (target/'payload.json').write_text(json.dumps(self.payload()), encoding='utf-8')
            (target/'facilities.html').write_bytes(analytics.content)
            for module in ('marketplace', 'services', 'users'):
                (target/f'{module}.html').write_bytes(self.client.get(reverse('admin_marketplace_analytics_page'), {'module': module, 'period': 'today'}).content)

    def test_analytics_permissions_and_invalid_periods(self):
        url = reverse('admin_marketplace_analytics_page')
        self.assertEqual(self.client.get(url, {'module': 'unknown'}).status_code, 400)
        self.assertEqual(self.client.get(url, {'module': 'services', 'period': 'custom', 'start_date': 'bad', 'end_date': 'bad'}).status_code, 400)
        self.client.force_login(self.marketplace_admin)
        for module in ('services', 'users', 'facilities'):
            self.assertEqual(self.client.get(url, {'module': module}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url, {'module': 'services'}).status_code, 302)

    def test_users_summary_uses_registration_dates_and_recorded_types_not_roles(self):
        from accounts.models import User
        from api.models import CampusHubUser
        from .dashboard_executive import users_overview
        from modules.marketplace.services.analytics import AnalyticsPeriod
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        web = User.objects.create_user(username='registered-web', email_verified=True,
            date_joined=timezone.make_aware(datetime(2026, 10, 4, 12)))
        for index, (kind, day, verified) in enumerate((('student', 4, False), ('faculty', 2, True), ('guest', 1, False), ('', 1, False))):
            mobile = CampusHubUser.objects.create(username=f'registered-mobile-{index}', email=f'registered-{index}@example.test',
                password_hash='sensitive-test-hash', first_name='Recorded', user_type=kind, role='Faculty', email_verified=verified)
            stamp = timezone.make_aware(datetime(2026, 10 if day > 1 else 9, day, 12))
            CampusHubUser.objects.filter(pk=mobile.pk).update(created_at=stamp)
        period = AnalyticsPeriod('custom', 'Test', date(2026, 10, 1), date(2026, 10, 4))
        with CaptureQueriesContext(connection) as queries:
            data = users_overview(period)
        self.assertEqual(len(queries), 4)
        self.assertEqual(data['new_registrations'], 3)
        self.assertEqual(data['verified_users'], 2)
        self.assertEqual([row['count'] for row in data['trend']], [0, 1, 0, 2])
        self.assertEqual({row['name']: row['count'] for row in data['distribution']}, {'Student': 1, 'Faculty': 1, 'Guest': 1})
        self.assertGreaterEqual(data['untyped'], 1)
        self.assertNotIn('active_users', data)
        self.assertNotIn('sensitive-test-hash', json.dumps(data))
        payload = self.payload()['executive']['users']
        self.assertEqual(payload['new_registrations'], 2)
        self.assertEqual(len(payload['trend']), 1)
        range_params = {'period': 'custom', 'start_date': '2026-10-01', 'end_date': '2026-10-04'}
        with patch('django.utils.timezone.localdate', return_value=self.today):
            response = self.client.get(reverse('admin_dashboard_api'), range_params)
        self.assertEqual(response.status_code, 200)
        range_payload = response.json()
        self.assertEqual([row['count'] for row in range_payload['executive']['users']['trend']], [0, 1, 0, 2])
        self.assertEqual(range_payload['executive']['users']['new_registrations'], 3)
        directory = os.environ.get('EXECUTIVE_REVIEW_DIR')
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            with patch('django.utils.timezone.localdate', return_value=self.today):
                page = self.client.get(reverse('admin_dashboard_page'), {'period': 'today'})
            (target/'users-populated.html').write_bytes(page.content)
            (target/'users-populated.json').write_text(json.dumps(self.payload()), encoding='utf-8')
            for label, params in (('range', range_params), ('week', {'period': 'last_7_days'}),
                                  ('calendar', {'period': 'custom', 'start_date': '2026-09-01', 'end_date': '2026-10-04'})):
                with patch('django.utils.timezone.localdate', return_value=self.today):
                    page = self.client.get(reverse('admin_dashboard_page'), params)
                    api = self.client.get(reverse('admin_dashboard_api'), params)
                self.assertEqual(page.status_code, 200)
                self.assertEqual(api.status_code, 200)
                (target/f'users-{label}.html').write_bytes(page.content)
                (target/f'users-{label}.json').write_text(json.dumps(api.json()), encoding='utf-8')

    def test_final_major_section_order_and_users_empty_states(self):
        with patch('django.utils.timezone.localdate', return_value=self.today):
            page = self.client.get(reverse('admin_dashboard_page'), {'period': 'today'})
        html = page.content.decode()
        anchors = ['id="systemOverviewTitle"', 'id="dashboardAttentionTitle"',
                   'id="marketplaceOverviewTitle"', 'id="facilitiesOverviewTitle"', 'id="servicesOverviewTitle"',
                   'id="usersOverviewTitle"', 'id="recentActivitiesTitle"']
        self.assertEqual([html.index(anchor) for anchor in anchors], sorted(html.index(anchor) for anchor in anchors))
        self.assertContains(page, 'No User Registration Data Yet')
        self.assertContains(page, 'No User Distribution Data')
        self.assertContains(page, 'View User Analytics')
        self.assertContains(page, 'id="userRegistrationView"', count=1)
        self.assertContains(page, 'value="daily" selected>Daily')
        self.assertContains(page, 'value="weekly">Weekly')
        self.assertContains(page, 'value="monthly">Monthly')
        self.assertNotContains(page, 'value="cumulative"')
        self.assertContains(page, 'aria-controls="userRegistrationTrendChart userRegistrationData"')
        start = html.index('<aside class="dashboard-summary-aside executive-bundle-panel"')
        panel = html[start:html.index('</aside>', start)]
        self.assertEqual(panel.count('<a '), 0)
        for label in ('Suggested Product Bundles', 'Overview of marketplace product bundle recommendations.',
                      'Saved product combinations will appear here when available.'):
            self.assertIn(label, panel)
        for action in ('Recommendation Activity', 'Sent to Sellers', 'Awaiting Seller Response', 'Bundles Created',
                       'View Recommendations', 'Create Bundle', 'Send to Seller', 'Approve Recommendation',
                       'Reject Recommendation', '>Lift<', '>Support<', '>Confidence<'):
            self.assertNotIn(action, panel)
        directory = os.environ.get('EXECUTIVE_REVIEW_DIR')
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            (target/'users-empty.html').write_bytes(page.content)
            (target/'users-empty.json').write_text(json.dumps(self.payload()), encoding='utf-8')

    def test_registration_daily_source_spans_calendar_year_and_week_boundaries(self):
        from accounts.models import User
        from api.models import CampusHubUser
        for name, stamp in (('year-edge-web', datetime(2025, 12, 31, 12)),
                            ('monday-edge-web', datetime(2026, 1, 5, 12))):
            User.objects.create_user(username=name, date_joined=timezone.make_aware(stamp))
        mobile = CampusHubUser.objects.create(username='year-edge-mobile', email='year-edge@example.test',
            password_hash='isolated-test-hash', first_name='Recorded', user_type='guest')
        CampusHubUser.objects.filter(pk=mobile.pk).update(created_at=timezone.make_aware(datetime(2026, 1, 1, 12)))
        params = {'period': 'custom', 'start_date': '2025-12-30', 'end_date': '2026-01-05'}
        with patch('django.utils.timezone.localdate', return_value=self.today):
            api = self.client.get(reverse('admin_dashboard_api'), params)
        self.assertEqual(api.status_code, 200)
        payload = api.json()
        self.assertEqual([row['count'] for row in payload['executive']['users']['trend']], [0, 1, 1, 0, 0, 0, 1])
        self.assertEqual(payload['executive']['users']['new_registrations'], 3)
        directory = os.environ.get('EXECUTIVE_REVIEW_DIR')
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            with patch('django.utils.timezone.localdate', return_value=self.today):
                page = self.client.get(reverse('admin_dashboard_page'), params)
            self.assertEqual(page.status_code, 200)
            (target/'users-boundary.html').write_bytes(page.content)
            (target/'users-boundary.json').write_text(json.dumps(payload), encoding='utf-8')

    def test_service_attention_displays_recorded_availability_status(self):
        self.service.availability_status = Facility.STATUS_MAINTENANCE
        self.service.save(update_fields=['availability_status'])
        rows = self.payload()['executive']['services']['attention']
        row = next(row for row in rows if row['reference'] == self.service.pk)
        self.assertEqual(row['status'], self.service.get_availability_status_display())
        self.assertIn('status=maintenance', row['url'])
