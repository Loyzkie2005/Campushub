"""Read-only audit preview/details and final executive page order."""
from datetime import date, datetime, time, timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from accounts.models import AccountActivity


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DashboardOperationsTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        self.client.force_login(self.super_admin)
        AccountActivity.objects.all().delete()

    def event(self, offset=0, result='success'):
        event = AccountActivity.objects.create(account_source='admin', account_id=self.super_admin.pk,
            full_name='Recorded target, not the actor', username='target-example', role='User',
            activity_type='service_updated', activity='Technical details should not be displayed', module='Services', result=result,
            metadata={'actor_admin_id': self.super_admin.pk, 'facility_id': self.fac_court.pk,
                      'password': 'DO_NOT_EXPOSE_PASSWORD', 'api_key': 'DO_NOT_EXPOSE_KEY',
                      'nested': {'token': 'DO_NOT_EXPOSE_TOKEN'}},
            ip_address='192.0.2.8', user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/155.0.0.0 SECRET_RAW_UA',
            session_identifier='DO_NOT_EXPOSE_SESSION')
        stamp = timezone.make_aware(datetime.combine(self.today, time(12))) + timedelta(minutes=offset)
        AccountActivity.objects.filter(pk=event.pk).update(created_at=stamp)
        return event

    def snapshot(self):
        with patch('django.utils.timezone.localdate', return_value=self.today):
            response = self.client.get(reverse('admin_dashboard_api'), {'period': 'today'})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_preview_is_bounded_ordered_readable_and_contains_no_connection_or_secrets(self):
        events = [self.event(index, 'failed' if index == 6 else 'success') for index in range(7)]
        rows = self.snapshot()['executive']['activities']
        self.assertEqual(len(rows), 5)
        self.assertEqual([row['details_url'] for row in rows], [reverse('activity_log_detail', args=[event.pk]) for event in reversed(events[2:])])
        self.assertEqual(rows[0]['result'], 'Failed')
        self.assertEqual(rows[0]['activity'], 'Service Updated')
        self.assertEqual(rows[0]['module'], 'Services')
        self.assertEqual(rows[0]['user'], self.super_admin.get_full_name() or self.super_admin.username)
        self.assertIn('Oct', rows[0]['time_label'])
        self.assertNotIn('T12:', rows[0]['time_label'])
        preview = json.dumps(rows)
        for value in ('DO_NOT_EXPOSE', 'SECRET_RAW_UA', '192.0.2.8', 'Technical details', 'Recorded target', 'metadata', 'session_identifier'):
            self.assertNotIn(value, preview)
        self.assertEqual(AccountActivity.objects.count(), 7)

    def test_existing_detail_api_provides_allowlisted_details_and_keeps_role_gate(self):
        event = self.event()
        url = reverse('activity_log_detail', args=[event.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']
        self.assertEqual(data['performed_by']['name'], self.super_admin.get_full_name() or self.super_admin.username)
        self.assertEqual(data['connection'], {'ip_address': '192.0.2.8', 'device': 'Windows Desktop', 'browser': 'Google Chrome'})
        self.assertEqual(data['affected_record']['name'], self.fac_court.facility_name)
        for value in ('DO_NOT_EXPOSE', 'SECRET_RAW_UA', 'session_identifier', 'metadata', 'password_hash'):
            self.assertNotIn(value, response.content.decode())
        self.assertEqual(self.client.post(url, {}).status_code, 405)
        self.client.force_login(self.facilities_admin)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 401)

    def test_preview_dates_keep_other_year_and_use_application_timezone(self):
        self.event()
        previous = self.event(-1)
        stamp = timezone.make_aware(datetime(2025, 12, 30, 16, 20))
        AccountActivity.objects.filter(pk=previous.pk).update(created_at=stamp)
        params = {'period': 'custom', 'start_date': '2025-12-30', 'end_date': self.today.isoformat()}
        with patch('django.utils.timezone.localdate', return_value=self.today):
            response = self.client.get(reverse('admin_dashboard_api'), params)
            page = self.client.get(reverse('admin_dashboard_page'), params)
        self.assertEqual(response.status_code, 200)
        rows = response.json()['executive']['activities']
        self.assertEqual([row['time_label'] for row in rows], ['Oct 4, 12:00 PM', 'Dec 30, 2025, 4:20 PM'])
        self.assertContains(page, 'Dec 30, 2025, 4:20 PM')
        self.assertContains(page, 'data-time-zone="Asia/Manila"')
        self.assertContains(page, 'audit-result-success')
        self.assertContains(page, 'audit-icon-button')
        self.assertContains(page, 'title="View Details"')
        self.assertContains(page, '<th scope="col">Result</th>')
        self.assertContains(page, '<th scope="col" class="audit-secondary">Module</th>')
        # Existing reports explicitly use Manila, independent of a caller override.
        with timezone.override('UTC'), patch('django.utils.timezone.localdate', return_value=self.today):
            utc = self.client.get(reverse('admin_dashboard_api'), params)
        self.assertEqual(utc.json()['executive']['activities'][0]['time_label'], 'Oct 4, 12:00 PM')
        self.assertEqual(AccountActivity.objects.count(), 2)

    def test_final_layout_empty_populated_and_export(self):
        directory = os.environ.get('OPERATIONS_REVIEW_DIR')
        for state in ('empty', 'populated'):
            if state == 'populated':
                for index in range(7):
                    self.event(index, 'failed' if index == 6 else 'success')
            with patch('django.utils.timezone.localdate', return_value=self.today):
                page = self.client.get(reverse('admin_dashboard_page'), {'period': 'today'})
            self.assertEqual(page.status_code, 200)
            html = page.content.decode()
            anchors = ['systemOverviewTitle', 'dashboardAttentionTitle', 'marketplaceRecommendationsTitle',
                       'marketplaceOverviewTitle', 'facilitiesOverviewTitle', 'servicesOverviewTitle', 'recentActivitiesTitle']
            self.assertEqual([html.index('id="'+key+'"') for key in anchors], sorted(html.index('id="'+key+'"') for key in anchors))
            for anchor in ('recentActivitiesTitle',):
                self.assertEqual(html.count('id="'+anchor+'"'), 1)
            for text in ('Recent System Activities', 'Latest important actions recorded across CampusHub.', 'No Recent System Activities',
                         'happening across CampusHub today.', 'View All Activities'):
                self.assertIn(text, html)
            self.assertNotIn('data-inline-system-status', html)
            self.assertNotIn('data-status-inline', html)
            self.assertEqual(html.count('id="dashboardSystemStatus"'), 0)
            self.assertEqual(html.count('data-system-service='), 0)
            self.assertNotIn('data-status-top', html)
            self.assertNotIn('data-status-footer', html)
            if state == 'populated':
                self.assertEqual(html.count('data-activity-detail-url='), 5)
                self.assertIn('Service Updated', html)
            self.assertEqual(self.client.get(reverse('admin_user_monitoring_page')).status_code, 200)
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                (target/f'operations-{state}.html').write_bytes(page.content)
                payload = self.snapshot()
                (target/f'operations-{state}.json').write_text(json.dumps(payload), encoding='utf-8')
                if payload['executive']['activities']:
                    detail = self.client.get(payload['executive']['activities'][0]['details_url'])
                    (target/'activity-detail.json').write_bytes(detail.content)
