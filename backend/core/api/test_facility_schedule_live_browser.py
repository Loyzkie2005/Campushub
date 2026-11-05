"""Opt-in real Chrome test using HTTP, normal login and disposable PostgreSQL."""
import json
import os
from pathlib import Path
import subprocess
from unittest import skipUnless

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.apps import apps
from django.db import connection

from accounts.models import User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, Facility
from modules.facilities.services.operating_schedule import WEEKDAYS


@skipUnless(os.environ.get('CAMPUSHUB_PLAYWRIGHT_MODULE'), 'Opt-in Chrome/Playwright test')
class FacilityScheduleLiveBrowserTests(StaticLiveServerTestCase):
    # Match the legacy unmanaged-table cascading test cleanup used by booking tests.
    available_apps = [config.name for config in apps.get_app_configs()]

    def test_real_form_clicks_roles_and_persistence(self):
        self.assertTrue(connection.settings_dict['NAME'].startswith('test_'))
        password = 'Isolated-Schedule-Browser-2026!'
        for username, role in [('schedule-super', 'Super Admin'),
                               ('schedule-facilities', 'Facilities Admin'),
                               ('schedule-market', 'Marketplace Admin')]:
            user = User.objects.create_user(username=username, password=password,
                role=role, is_staff=True, is_superuser=role == 'Super Admin')
            sync_user_admin_permissions(user)
        daily = {day: {'open': '08:00', 'close': '17:00'} for day in WEEKDAYS}
        weekend = {day: daily[day] if day in WEEKDAYS[5:] else None for day in WEEKDAYS}
        for pk, category, workflow in [
            ('BROWSER-COURT', 'covered_court', {'weekend_only': True, 'operating_hours': weekend,
                                             'allowed_booking_days': ['sunday']}),
            ('BROWSER-HALL', 'function_hall', {'operating_hours': daily}),
        ]:
            Facility.objects.create(id=pk, facility_name=pk, facility_type=category,
                booking_mode='slot', rate='500', price_type='hour', capacity=50,
                location='Isolated browser fixture', availability_status='available',
                workflow_config=workflow)
        output = Path(os.environ['SCHEDULE_LIVE_OUT'])
        output.mkdir(parents=True, exist_ok=True)
        before_bookings = Booking.objects.count()
        env = {**os.environ, 'SCHEDULE_LIVE_URL': self.live_server_url,
               'SCHEDULE_TEST_PASSWORD': password}
        self.assertEqual(self.client.get('/').status_code, 200)
        script = Path(__file__).with_name('facility_schedule_live_browser_checks.cjs')
        result = subprocess.run(['node', str(script)], env=env, capture_output=True,
            text=True, timeout=300, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = json.loads((output / 'results.json').read_text(encoding='utf-8'))
        print(json.dumps(evidence))
        self.assertEqual(Booking.objects.count(), before_bookings)
        saved = Facility.objects.get(pk='BROWSER-COURT').workflow_config
        self.assertEqual(saved['operating_hours'], {day: daily[day] if day in WEEKDAYS[:5] else None for day in WEEKDAYS})
        self.assertNotIn('weekend_only', saved)
        self.assertNotIn('allowed_booking_days', saved)
