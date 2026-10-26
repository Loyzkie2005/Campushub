"""Operational status snapshots must not be inferred from booking occupancy."""
from datetime import date, time
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts import tests as fixtures
from api.models import Booking, Facility
from .dashboard_facility_status import facility_operational_status


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FacilityOperationalStatusTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 7)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        self.client.force_login(self.super_admin)

    def api(self, params=None):
        with patch("django.utils.timezone.localdate", return_value=self.today):
            return self.client.get(reverse("admin_dashboard_api"), params or {}).json()

    def add_facility(self, status, **fields):
        return Facility.objects.create(id=f"status-{Facility.objects.count()}",
            facility_name="Status Test Facility", availability_status=status, **fields)

    def test_all_operational_counts_and_no_extra_queries(self):
        self.add_facility(Facility.STATUS_AVAILABLE)
        self.add_facility(Facility.STATUS_AVAILABLE)
        self.add_facility(Facility.STATUS_UNAVAILABLE)
        self.add_facility(Facility.STATUS_MAINTENANCE)
        rows = list(Facility.objects.all())
        with CaptureQueriesContext(connection) as queries:
            status = facility_operational_status(rows)
        self.assertEqual(len(queries), 0)
        self.assertEqual(status["total"], 5)
        self.assertEqual([row["count"] for row in status["rows"]], [3, 1, 1, 0])
        self.assertEqual([row["label"] for row in status["rows"]], [label for _, label in Facility.STATUS_CHOICES])

    def test_archived_and_legacy_states_use_existing_disable_rules(self):
        self.add_facility(Facility.STATUS_AVAILABLE, is_archived=True)
        self.add_facility(Facility.STATUS_INACTIVE)
        self.add_facility(Facility.STATUS_OCCUPIED)
        self.add_facility(Facility.STATUS_RESERVED)
        status = self.api()["facilities"]["operational_status"]
        self.assertEqual([row["count"] for row in status["rows"]], [1, 2, 0, 2])
        self.assertEqual(status["total"], 5)
        self.assertNotIn("Occupied", [row["label"] for row in status["rows"]])
        # Presentation does not rewrite the existing database status.
        self.assertTrue(Facility.objects.filter(availability_status=Facility.STATUS_OCCUPIED).exists())

    def test_unknown_or_blank_stored_states_are_errors_not_zero_counts(self):
        for value in ("invalid_status", ""):
            Facility.objects.filter(pk=self.fac_court.pk).update(availability_status=value)
            self.assertEqual(self.api()["facilities"]["operational_status"], {"state": "error"})

    def test_bookings_groupings_and_reporting_dates_do_not_change_operational_counts(self):
        expected = self.api()["facilities"]["operational_status"]
        for index, status in enumerate((Booking.STATUS_PENDING, Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED)):
            Booking.objects.create(id=f"status-booking-{index}", facility=self.fac_court,
                booking_date=self.today, start_time=time(13), end_time=time(17), status=status)
        for period in ("today", "previous_month", "custom"):
            for grouping in ("daily", "weekly", "monthly"):
                data = self.api({"period": period, "booking_grouping": grouping,
                    "sales_grouping": grouping, "start_date": "2026-09-01", "end_date": "2026-09-20"})
                self.assertEqual(data["facilities"]["operational_status"], expected)
        self.assertGreater(self.api()["facilities"]["schedule_conflicts"], 0)

    def test_real_markup_empty_singular_populated_error_and_export(self):
        directory = os.environ.get("FACILITY_STATUS_TEST_DIR")
        Booking.objects.all().delete()
        Facility.objects.all().delete()
        for state in ("empty", "single", "populated", "error"):
            if state == "single":
                self.add_facility(Facility.STATUS_AVAILABLE)
            elif state == "populated":
                self.add_facility(Facility.STATUS_AVAILABLE)
                self.add_facility(Facility.STATUS_AVAILABLE)
                self.add_facility(Facility.STATUS_UNAVAILABLE)
                self.add_facility(Facility.STATUS_MAINTENANCE)
            elif state == "error":
                self.add_facility("invalid_status")
            with patch("django.utils.timezone.localdate", return_value=self.today):
                page = self.client.get(reverse("admin_facility_analytics_page"))
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, 'data-facility-operational-status', count=1)
            self.assertNotContains(page, 'id="facilityScheduleConflicts"')
            self.assertNotContains(page, 'id="facilityAvailabilityOccupied"')
            if state == "single": self.assertContains(page, 'data-operational-unit>Facility</span>')
            payload = self.api()
            status = payload["facilities"]["operational_status"]
            self.assertEqual(status["state"], "ready" if state in ("single", "populated") else state)
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                (target / f"{state}.source.html").write_bytes(page.content)
                (target / f"{state}.json").write_text(json.dumps(payload), encoding="utf-8")
