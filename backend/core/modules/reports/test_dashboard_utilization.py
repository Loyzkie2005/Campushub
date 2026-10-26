from datetime import date, time
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.db import DatabaseError, connection
from django.test.utils import CaptureQueriesContext
from django.template.loader import render_to_string
from django.urls import reverse

from accounts import tests as fixtures
from api.models import Booking, Facility, Room
from .dashboard_utilization import build_facility_utilization


class FacilityUtilizationTests(fixtures.DedicatedDomainDashboardTests):
    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        Booking.objects.all().delete()
        Facility.objects.all().update(is_archived=True)
        self.period = SimpleNamespace(start=date(2026, 10, 1), end=date(2026, 10, 2), days=2)
        self.sequence = 0
        self.client.force_login(self.super_admin)

    def facility(self, key, **fields):
        self.sequence += 1
        return Facility.objects.create(id=f'usage-fac-{self.sequence}', facility_name=key,
                                       facility_type=key, **fields)

    def booking(self, facility, **fields):
        self.sequence += 1
        fields.setdefault('booking_date', self.period.start)
        fields.setdefault('status', 'approved')
        return Booking.objects.create(id=f'usage-book-{self.sequence}', facility=facility, **fields)

    def row(self, key):
        return next(row for row in build_facility_utilization(self.period)['rows'] if row['key'] == key)

    def test_hours_clip_to_schedule_merge_overlap_and_exclude_invalid_statuses(self):
        court = self.facility('covered_court', workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        self.booking(court, start_time=time(7), end_time=time(11))
        self.booking(court, start_time=time(10), end_time=time(12), status='completed')
        for status in ('pending', 'rejected', 'cancelled'):
            self.booking(court, start_time=time(8), end_time=time(18), status=status)
        self.booking(court, booking_date=date(2026, 9, 30), start_time=time(8), end_time=time(18))
        row = self.row('covered_court')
        self.assertEqual((row['used'], row['capacity'], row['percentage']), (4, 20, 20))

    def test_maintenance_and_academic_blocks_remove_capacity_and_usage(self):
        hall = self.facility('function_hall', workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        self.booking(hall, purpose='[maintenance] repair', start_time=time(8), end_time=time(10))
        self.booking(hall, purpose='[class] lecture', start_time=time(10), end_time=time(12))
        self.booking(hall, start_time=time(8), end_time=time(14))
        row = self.row('function_hall')
        self.assertEqual((row['used'], row['capacity'], row['percentage']), (2, 16, 12.5))

    def test_hostel_uses_room_nights_checkout_exclusive_and_union(self):
        hostel = self.facility('hostel', rooms_units=99)
        room = Room.objects.create(id=uuid4(), facility=hostel, room_name='A')
        Room.objects.create(id=uuid4(), facility=hostel, room_name='B')
        excluded = Room.objects.create(id=uuid4(), facility=hostel, status='maintenance')
        self.booking(hostel, booking_date=None, room_id=room.id, check_in_date=date(2026, 9, 30), check_out_date=date(2026, 10, 2))
        self.booking(hostel, booking_date=None, room_id=room.id, check_in_date=date(2026, 10, 1), check_out_date=date(2026, 10, 2), status='completed')
        self.booking(hostel, booking_date=None, room_id=excluded.id, check_in_date=date(2026, 10, 1), check_out_date=date(2026, 10, 3))
        row = self.row('hostel')
        self.assertEqual((row['used'], row['capacity'], row['percentage']), (1, 4, 25))

    def test_hostel_maintenance_room_nights_and_missing_assignment(self):
        hostel = self.facility('hostel')
        room = Room.objects.create(id=uuid4(), facility=hostel)
        self.booking(hostel, purpose='[maintenance]', booking_date=None, room_id=room.id,
                     check_in_date=date(2026, 10, 1), check_out_date=date(2026, 10, 2))
        self.assertEqual(self.row('hostel')['capacity'], 1)
        self.booking(hostel, booking_date=None, check_in_date=date(2026, 10, 1), check_out_date=date(2026, 10, 3))
        self.assertEqual(self.row('hostel')['state'], 'unavailable')

    def test_slots_count_each_reserved_slot_once_and_remove_blocked_slots(self):
        kitchen = self.facility('training_kitchen', slots='08:00-10:00; 10:00-12:00')
        self.booking(kitchen, start_time=time(8), end_time=time(9))
        self.booking(kitchen, start_time=time(8), end_time=time(10), status='completed')
        self.booking(kitchen, purpose='[maintenance]', start_time=time(10), end_time=time(12))
        self.booking(kitchen, booking_date=self.period.end, start_time=time(8), end_time=time(12), status='pending')
        row = self.row('training_kitchen')
        self.assertEqual((row['used'], row['capacity'], row['percentage']), (1, 3, 33.3))

    def test_lease_units_are_distinct_in_the_period_not_booking_count(self):
        lease = self.facility('lease_space', rooms_units=10)
        unit = uuid4()
        for _ in range(2):
            self.booking(lease, booking_date=None, room_id=unit,
                         check_in_date=date(2026, 9, 1), check_out_date=date(2026, 11, 1))
        self.booking(lease, booking_date=None, room_id=uuid4(), status='cancelled',
                     check_in_date=date(2026, 9, 1), check_out_date=date(2026, 11, 1))
        row = self.row('lease_space')
        self.assertEqual((row['used'], row['capacity'], row['percentage']), (1, 10, 10))

    def test_no_fake_service_capacity_zero_capacity_and_incomplete_group(self):
        self.facility('food_analysis', capacity=100)
        self.facility('lease_space', rooms_units=0)
        self.facility('training_kitchen', capacity=100)
        self.facility('covered_court', workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        self.facility('covered_court')
        summary = build_facility_utilization(self.period)
        for row in summary['rows']:
            self.assertIsNone(row['percentage'])
            self.assertEqual(row['state'], 'unavailable')

    def test_incomplete_operating_text_never_assumes_eight_hours(self):
        self.facility('covered_court', workflow_config={'operating_hours': 'Monday-Saturday 8:30am'})
        row = self.row('covered_court')
        self.assertIsNone(row['percentage'])
        self.assertIn('opening and closing', row['context'])

    def test_unavailable_archived_capacity_and_lease_inventory(self):
        self.facility('covered_court', availability_status='inactive', workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        self.facility('function_hall', is_archived=True, workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        lease = self.facility('lease_space', rooms_units=100)
        room = Room.objects.create(id=uuid4(), facility=lease)
        Room.objects.create(id=uuid4(), facility=lease, status='maintenance')
        self.booking(lease, room_id=room.id, booking_date=None, check_in_date=date(2026, 10, 1), check_out_date=date(2026, 10, 3))
        self.assertIsNone(self.row('covered_court')['percentage'])
        self.assertEqual(self.row('function_hall')['facility_count'], 0)
        self.assertEqual(self.row('lease_space')['percentage'], 100)

    def test_bounded_queries_empty_and_database_failure_are_distinct(self):
        self.facility('hostel')
        with CaptureQueriesContext(connection) as queries:
            build_facility_utilization(self.period)
        self.assertLessEqual(len(queries), 3)
        Facility.objects.all().update(is_archived=True)
        empty = build_facility_utilization(self.period)
        self.assertEqual(empty['state'], 'empty')
        self.assertFalse(empty['has_usage'])
        if os.environ.get('FACILITY_UTILIZATION_REVIEW_DIR'):
            target = Path(os.environ['FACILITY_UTILIZATION_REVIEW_DIR']); target.mkdir(parents=True, exist_ok=True)
            (target / 'facility-utilization-empty.json').write_text(json.dumps(empty), encoding='utf-8')
        with patch('modules.reports.dashboard_utilization.Facility.objects.filter', side_effect=DatabaseError('test unavailable')), self.assertLogs('modules.reports.dashboard_utilization', level='ERROR'):
            self.assertEqual(build_facility_utilization(self.period)['state'], 'error')

    def test_no_usage_renders_text_without_visible_rows(self):
        court = self.facility('covered_court', workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        self.booking(court, status=Booking.STATUS_PENDING, start_time=time(8), end_time=time(13))
        summary = build_facility_utilization(self.period)
        self.assertFalse(summary['has_usage'])
        self.assertEqual(summary['rows'][0]['percentage'], 0)
        html = render_to_string('dashboard/partials/facility_utilization.html', {'facility_analytics': {'utilization_summary': summary}})
        self.assertIn('id="facilityUtilizationList" hidden', html)
        self.assertIn('data-utilization-empty>', html)
        self.assertIn('No facility utilization data yet.', html)
        self.assertNotIn('<svg', html)
        self.assertNotIn('Utilization appears after valid usage and capacity are configured.', html)
        # The explicit sample fixture is UI-only and does not create records.
        self.assertEqual(Booking.objects.filter(facility=court).count(), 1)

    def test_api_global_dates_render_and_export_preview(self):
        court = self.facility('covered_court', workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        self.booking(court, start_time=time(8), end_time=time(13))
        for end, expected in (('2026-10-01', 50), ('2026-10-02', 25)):
            response = self.client.get(reverse('admin_dashboard_api'), {'period': 'custom', 'start_date': '2026-10-01', 'end_date': end})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['facilities']['utilization'][0]['percentage'], expected)
        hall = self.facility('function_hall', workflow_config={'operating_hours': 'Daily 08:00-18:00'})
        self.booking(hall, start_time=time(8), end_time=time(12))
        hostel = self.facility('hostel')
        room = Room.objects.create(id=uuid4(), facility=hostel)
        Room.objects.create(id=uuid4(), facility=hostel)
        self.booking(hostel, booking_date=None, room_id=room.id, check_in_date=self.period.start, check_out_date=date(2026, 10, 3))
        self.facility('food_analysis')
        kitchen = self.facility('training_kitchen', slots='08:00-10:00; 10:00-12:00')
        self.booking(kitchen, start_time=time(8), end_time=time(10))
        lease = self.facility('lease_space', rooms_units=10)
        for _ in range(2):
            self.booking(lease, booking_date=None, room_id=uuid4(), check_in_date=self.period.start, check_out_date=date(2026, 10, 3))
        summary = build_facility_utilization(self.period)
        self.assertTrue(summary['has_usage'])
        html = render_to_string('dashboard/partials/facility_utilization.html', {'facility_analytics': {'utilization_summary': summary}})
        self.assertIn('aria-valuenow="25.0"', html)
        self.assertIn('Utilization unavailable', html)
        folder = os.environ.get('FACILITY_UTILIZATION_REVIEW_DIR')
        if folder:
            target = Path(folder); target.mkdir(parents=True, exist_ok=True)
            (target / 'facility-utilization.source.html').write_text(html, encoding='utf-8')
            (target / 'facility-utilization.json').write_text(json.dumps(summary), encoding='utf-8')
