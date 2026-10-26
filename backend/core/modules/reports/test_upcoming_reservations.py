"""Reservation selection, truthful display and global dashboard integration."""
from datetime import date, datetime, time, timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts import tests as fixtures
from api.models import Booking, Facility
from .dashboard_bookings import upcoming_reservations


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class UpcomingReservationsTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 7)
    now = datetime(2026, 10, 7, 10, tzinfo=ZoneInfo("Asia/Manila"))

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        Booking.objects.all().delete()
        self.client.force_login(self.super_admin)

    def booking(self, **fields):
        defaults = {"id": f"upcoming-{Booking.objects.count()}", "facility": self.fac_court,
                    "booking_date": self.today + timedelta(days=1), "status": Booking.STATUS_APPROVED}
        defaults.update(fields)
        return Booking.objects.create(**defaults)

    def rows(self):
        return upcoming_reservations(today=self.today, now=self.now)

    def api(self, params=None):
        with patch("django.utils.timezone.localdate", return_value=self.today), patch("django.utils.timezone.now", return_value=self.now):
            return self.client.get(reverse("admin_dashboard_api"), params or {}).json()

    def test_only_approved_future_assigned_reservations(self):
        valid = self.booking()
        for status in (Booking.STATUS_PENDING, Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED, Booking.STATUS_COMPLETED):
            self.booking(status=status)
        self.booking(booking_date=self.today - timedelta(days=1))
        self.booking(booking_date=self.today, start_time=time(9), end_time=time(12))
        self.booking(facility=None)
        self.booking(booking_date=None)
        self.assertEqual([row["id"] for row in self.rows()], [valid.pk])
        self.assertEqual(self.rows()[0]["status_label"], "Approved")

    def test_nearest_five_mixed_reservations_and_one_query(self):
        hostel = Facility.objects.create(id="upcoming-hostel", facility_name="A Hostel", facility_type=Facility.TYPE_HOSTEL)
        far = self.booking(booking_date=self.today + timedelta(days=20))
        late = self.booking(booking_date=self.today, start_time=time(14), end_time=time(16))
        early = self.booking(booking_date=self.today, start_time=time(11), end_time=time(12))
        stay = self.booking(facility=hostel, booking_date=None, check_in_date=self.today + timedelta(days=2), check_out_date=self.today + timedelta(days=4))
        tomorrow = self.booking()
        last = self.booking(booking_date=self.today + timedelta(days=3))
        with CaptureQueriesContext(connection) as queries:
            rows = self.rows()
        self.assertEqual(len(queries), 1)
        self.assertEqual([row["id"] for row in rows], [early.pk, late.pk, tomorrow.pk, stay.pk, last.pk])
        self.assertNotIn(far.pk, [row["id"] for row in rows])
        self.assertIn("11:00 AM – 12:00 PM", rows[0]["when"])
        self.assertEqual(rows[3]["when"], "Oct 09–11, 2026")

    def test_stay_dates_authoritative_and_invalid_or_started_stays_excluded(self):
        for start, end in ((-1, 1), (0, 0), (2, 1)):
            self.booking(check_in_date=self.today + timedelta(days=start), check_out_date=self.today + timedelta(days=end))
        self.booking(check_in_date=self.today + timedelta(days=1), check_out_date=None)
        self.booking(check_in_date=None, check_out_date=self.today + timedelta(days=2))
        valid = self.booking(booking_date=self.today - timedelta(days=30), check_in_date=self.today, check_out_date=self.today + timedelta(days=2), start_time=time(1), end_time=time(2))
        self.assertEqual(self.rows(), [{"id": valid.pk, "facility": self.fac_court.facility_name,
            "requester": "Not recorded",
            "url": reverse("admin_booking_details_page", kwargs={"booking_id": valid.pk}),
            "when": "Oct 07–9, 2026", "status": "approved", "status_label": "Approved"}])

    def test_client_uses_existing_requester_formatter_without_extra_queries(self):
        self.booking(purpose='[reservation] Reserved by: Recorded campus client\nWorkshop')
        with CaptureQueriesContext(connection) as queries:
            rows = self.rows()
        self.assertEqual(len(queries), 1)
        self.assertEqual(rows[0]['requester'], 'Recorded campus client')

    def test_no_fake_times_and_stay_month_year_boundaries(self):
        undated_time = self.booking(booking_date=self.today)
        partial_time = self.booking(start_time=time(13), end_time=None)
        self.booking(booking_date=None, check_in_date=date(2026, 10, 31), check_out_date=date(2026, 11, 2))
        self.booking(booking_date=None, check_in_date=date(2026, 12, 31), check_out_date=date(2027, 1, 2))
        rows = self.rows()
        self.assertEqual([row["when"] for row in rows], ["Oct 07, 2026", "Oct 08, 2026", "Oct 31–Nov 02, 2026", "Dec 31, 2026–Jan 02, 2027"])
        self.assertEqual([row["id"] for row in rows[:2]], [undated_time.pk, partial_time.pk])

    def test_local_midnight_cutoff_and_stable_same_time_ties(self):
        from datetime import timezone as dt_timezone
        yesterday = self.booking(booking_date=self.today - timedelta(days=1), start_time=time(23))
        first = self.booking(id="upcoming-a", booking_date=self.today, start_time=time(1))
        second = self.booking(id="upcoming-b", booking_date=self.today, start_time=time(1))
        # 16:30 UTC on Oct 6 is 00:30 Manila on Oct 7.
        rows = upcoming_reservations(now=datetime(2026, 10, 6, 16, 30, tzinfo=dt_timezone.utc))
        self.assertEqual([row["id"] for row in rows], [first.pk, second.pk])
        self.assertNotIn(yesterday.pk, [row["id"] for row in rows])

    def test_reporting_periods_and_chart_groupings_keep_current_upcoming_snapshot(self):
        self.booking()
        expected = self.rows()
        for period in ("today", "last_7_days", "last_30_days", "this_month", "previous_month", "this_year", "custom"):
            for grouping in ("daily", "weekly", "monthly"):
                data = self.api({"period": period, "start_date": "2026-09-01", "end_date": "2026-09-20",
                                 "booking_grouping": grouping, "sales_grouping": grouping})
                self.assertEqual(data["facilities"]["upcoming_reservations"], expected)

    def test_empty_populated_initial_markup_calendar_and_export(self):
        directory = os.environ.get("UPCOMING_TEST_DIR")
        for state in ("empty", "populated"):
            if state == "populated":
                names = ("Covered Court", "Function Hall", "Hostel", "Training / Assessment Center", "Food Analysis Hub")
                for index, name in enumerate(names):
                    facility = Facility.objects.create(id=f"upcoming-preview-{index}", facility_name=name)
                    if index == 2:
                        self.booking(facility=facility, booking_date=None, check_in_date=self.today + timedelta(days=index + 1), check_out_date=self.today + timedelta(days=index + 3))
                    else:
                        self.booking(facility=facility, booking_date=self.today + timedelta(days=index + 1), start_time=time(13), end_time=time(17))
            with patch("django.utils.timezone.localdate", return_value=self.today), patch("django.utils.timezone.now", return_value=self.now):
                page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, 'data-upcoming-reservations', count=1)
            self.assertContains(page, f'href="{reverse("admin_calendar_page")}"')
            self.assertContains(page, "No Upcoming Reservations")
            payload = self.api({"period": "today"})
            rows = payload["facilities"]["upcoming_reservations"]
            self.assertEqual(len(rows), 5 if state == "populated" else 0)
            for row in rows:
                self.assertContains(page, row["facility"])
                self.assertContains(page, row["when"])
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                (target / f"{state}.source.html").write_bytes(page.content)
                (target / f"{state}.json").write_text(json.dumps(payload), encoding="utf-8")
