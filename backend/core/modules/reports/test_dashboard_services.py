"""Service-only executive summaries over real isolated request/catalog records."""
from datetime import date, datetime, time, timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from api.models import Booking, Facility


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DashboardServicesTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        Booking.objects.all().delete()
        self.client.force_login(self.super_admin)
        self.lab = Facility.objects.create(id='SV-LAB', facility_name='Laboratory Food Analysis',
            facility_type='food_analysis', booking_mode='service')
        self.assessment = Facility.objects.create(id='SV-ASSESS', facility_name='Assessment registration',
            facility_type='other', booking_mode='assessment')
        self.lease = Facility.objects.create(id='SV-LEASE', facility_name='Commercial Space',
            facility_type='lease_space', booking_mode='lease')

    def request_record(self, resource, status=Booking.STATUS_PENDING, day=None, key=None, **fields):
        row = Booking.objects.create(id=key or f'SV-{Booking.objects.count()}', facility=resource,
            user=self.ch_user, status=status, **fields)
        Booking.objects.filter(pk=row.pk).update(created_at=timezone.make_aware(
            datetime.combine(day or self.today, time(12))))
        return row

    def payload(self, **params):
        with patch('django.utils.timezone.localdate', return_value=self.today):
            response = self.client.get(reverse('admin_dashboard_api'), {'period': 'today', **params})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_status_counts_all_request_chart_distribution_and_physical_exclusions(self):
        for status in dict(Booking.STATUS_CHOICES):
            self.request_record(self.lab, status)
        self.request_record(self.assessment, Booking.STATUS_APPROVED)
        self.request_record(self.lease, Booking.STATUS_PENDING)
        self.request_record(self.fac_court, Booking.STATUS_APPROVED)
        self.request_record(self.lab, Booking.STATUS_PENDING, purpose='[class] Not a service request')
        self.request_record(self.lab, Booking.STATUS_COMPLETED, day=date(2026, 9, 1))
        services = self.payload()['executive']['services']
        self.assertEqual((services['total_requests'], services['open_requests'], services['pending_requests'], services['completed_requests']), (7, 4, 2, 1))
        self.assertEqual(sum(row['count'] for row in services['request_trend']['trend']), 7)
        self.assertEqual([(row['facility_id'], row['total']) for row in services['requests_by_service']],
                         [(self.lab.pk, 5), (self.assessment.pk, 1), (self.lease.pk, 1)])
        self.assertEqual(len(services['recent_requests']), 5)
        self.assertTrue(all(row['service'] != self.fac_court.facility_name for row in services['recent_requests']))
        self.assertNotIn('email', json.dumps(services['recent_requests']).lower())

    def test_service_grouping_period_boundaries_and_current_attention(self):
        self.request_record(self.lab, day=date(2026, 9, 1))
        for day in (date(2026, 9, 29), date(2026, 10, 1), self.today):
            self.request_record(self.assessment, Booking.STATUS_COMPLETED, day=day)
        for grouping, buckets in (('daily', 7), ('weekly', 1), ('monthly', 2)):
            data = self.payload(period='last_7_days', service_grouping=grouping, grouping='weekly', booking_grouping='monthly')
            services = data['executive']['services']
            self.assertEqual(services['active_services'], 3)
            self.assertEqual(services['completed_requests'], 3)
            self.assertEqual(services['pending_requests'], 0)
            self.assertEqual(services['pending_current'], 1)
            self.assertEqual(services['attention'][0]['status'], 'Pending')
            self.assertEqual(services['request_trend']['grouping'], grouping)
            self.assertEqual(len(services['request_trend']['trend']), buckets)
            self.assertEqual(sum(row['count'] for row in services['request_trend']['trend']), 3)
            self.assertEqual(data['facilities']['booking_overview']['grouping'], 'monthly')
        empty = self.payload(period='custom', start_date='2026-08-01', end_date='2026-08-03')['executive']['services']
        self.assertEqual(empty['active_services'], 3)
        self.assertEqual(empty['total_requests'], 0)
        self.assertEqual(empty['requests_by_service'], [])
        self.assertEqual(len(empty['attention']), 1)
        self.assertEqual(self.payload(service_grouping='bad')['executive']['services']['request_trend']['grouping'], 'daily')

    def test_distribution_identity_limit_latest_order_and_service_only_attention(self):
        for index in range(6):
            resource = Facility.objects.create(id=f'SV-EXTRA-{index}', facility_name='Same service name', booking_mode='service')
            for _ in range(index + 1):
                self.request_record(resource, Booking.STATUS_COMPLETED)
        for resource in (self.lab, self.assessment):
            Facility.objects.filter(pk=resource.pk).update(availability_status=Facility.STATUS_UNAVAILABLE)
        Facility.objects.filter(pk=self.lease.pk).update(is_archived=True, availability_status=Facility.STATUS_UNAVAILABLE)
        Facility.objects.filter(pk=self.fac_court.pk).update(availability_status=Facility.STATUS_UNAVAILABLE)
        for offset in range(7):
            self.request_record(self.lab, day=self.today-timedelta(days=offset))
        data = self.payload(period='last_30_days')['executive']['services']
        self.assertEqual(len(data['requests_by_service']), 5)
        totals = [row['total'] for row in data['requests_by_service']]
        self.assertEqual(totals, sorted(totals, reverse=True))
        self.assertEqual(len({row['facility_id'] for row in data['requests_by_service']}), 5)
        self.assertEqual(len(data['recent_requests']), 5)
        stamps = [row['submitted_at'] for row in data['recent_requests']]
        self.assertEqual(stamps, sorted(stamps, reverse=True))
        self.assertEqual(len(data['attention']), 5)
        self.assertEqual(sum(row['status'] == 'Temporarily Unavailable' for row in data['attention']), 2)
        self.assertTrue(all(row['reference'] != self.lease.pk and row['service'] != self.fac_court.facility_name for row in data['attention']))

    def test_layout_empty_states_routes_and_export(self):
        directory = os.environ.get('SERVICES_REVIEW_DIR')
        for state in ('empty', 'populated'):
            if state == 'populated':
                for resource in (self.lab, self.assessment, self.lease):
                    for status in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED):
                        self.request_record(resource, status)
                Facility.objects.filter(pk=self.lease.pk).update(availability_status=Facility.STATUS_UNAVAILABLE)
            with patch('django.utils.timezone.localdate', return_value=self.today):
                page = self.client.get(reverse('admin_dashboard_page'), {'period': 'today'})
            self.assertEqual(page.status_code, 200)
            html = page.content.decode()
            section = html[html.index('<section class="executive-section executive-services"'):html.index('aria-labelledby="recentActivitiesTitle"')]
            for title in ('Service Summary', 'Service Request Trend', 'Requests by Service', 'Recent Service Requests', 'Service Attention',
                          'No Service Request Data Yet', 'No Service Request Activity Yet', 'No Recent Service Requests', 'No Service Attention Needed'):
                self.assertIn(title, section)
            self.assertNotIn('Upcoming Bookings', section)
            self.assertNotIn('Most Requested Service', section)
            self.assertNotIn('operationalAttentionTitle', html)
            self.assertEqual(section.count('data-service-metric='), 4)
            data = self.payload()
            for url in (reverse('admin_services_page'), reverse('admin_service_requests_page'), data['executive']['analytics_urls']['services']):
                self.assertEqual(self.client.get(url).status_code, 200)
            for row in data['executive']['services']['recent_requests']:
                self.assertEqual(self.client.get(row['url']).status_code, 200)
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                (target/f'services-{state}.html').write_bytes(page.content)
                (target/f'services-{state}.json').write_text(json.dumps(data), encoding='utf-8')
                if state == 'populated':
                    for grouping in ('weekly', 'monthly'):
                        (target/f'services-populated-{grouping}.json').write_text(json.dumps(self.payload(service_grouping=grouping)), encoding='utf-8')
