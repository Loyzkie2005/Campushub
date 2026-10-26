"""Real ranking, reservation dates, exclusion rules and dashboard integration."""
from datetime import date, timedelta
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
from .dashboard_bookings import most_booked_facilities
from .dashboard_periods import resolve_dashboard_period


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class MostBookedFacilitiesTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        Booking.objects.all().delete()
        self.client.force_login(self.super_admin)

    def booking(self, facility=None, day=None, status=Booking.STATUS_APPROVED, **fields):
        return Booking.objects.create(id=f"ranking-{Booking.objects.count()}",
            facility=facility or self.fac_court, booking_date=day or self.today,
            status=status, **fields)

    def api(self, params=None):
        with patch("django.utils.timezone.localdate", return_value=self.today):
            return self.client.get(reverse("admin_dashboard_api"), params or {}).json()

    def test_top_five_statuses_period_orphans_and_one_query(self):
        facilities = [Facility.objects.create(id=f"ranking-facility-{i}",
            facility_name=f"Ranking Facility {i}") for i in range(6)]
        for i, facility in enumerate(facilities, 1):
            for count in range(i):
                self.booking(facility, status=Booking.STATUS_APPROVED if count % 2 else Booking.STATUS_COMPLETED)
        for status in (Booking.STATUS_PENDING, Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED):
            for _ in range(8):
                self.booking(facilities[0], status=status)
        self.booking(facilities[0], day=self.today - timedelta(days=30))
        Booking.objects.create(id="ranking-orphan", facility=None, booking_date=self.today, status=Booking.STATUS_APPROVED)
        period, _ = resolve_dashboard_period({"period": "today"}, self.today)
        with CaptureQueriesContext(connection) as queries:
            rows = most_booked_facilities(period)
        self.assertEqual(len(queries), 1)
        self.assertEqual([row["id"] for row in rows], [facility.pk for facility in reversed(facilities[1:])])
        self.assertEqual([row["bookings"] for row in rows], [6, 5, 4, 3, 2])
        self.assertEqual([row["rank"] for row in rows], [1, 2, 3, 4, 5])

    def test_stays_overlap_checkout_exclusive_and_invalid_stays_excluded(self):
        hostel = Facility.objects.create(id="ranking-hostel", facility_name="Ranking accommodation", facility_type=Facility.TYPE_HOSTEL)
        stays = ((-3, 2), (0, 1), (-2, 0), (1, 3), (0, 0), (2, 1))
        for index, (start, end) in enumerate(stays):
            Booking.objects.create(id=f"ranking-stay-{index}", facility=hostel,
                booking_date=None, check_in_date=self.today + timedelta(days=start),
                check_out_date=self.today + timedelta(days=end), status=Booking.STATUS_APPROVED)
        period, _ = resolve_dashboard_period({"period": "today"}, self.today)
        self.assertEqual(most_booked_facilities(period)[0]["bookings"], 2)

    def test_images_reuse_first_uploaded_image_in_one_query_and_initial_html(self):
        self.fac_court.image_url = json.dumps(["/media/facilities/court.jpg", "/media/facilities/second.jpg"])
        self.fac_court.save(update_fields=["image_url"])
        for _ in range(3):
            self.booking()
        period, _ = resolve_dashboard_period({"period": "today"}, self.today)
        with CaptureQueriesContext(connection) as queries:
            rows = most_booked_facilities(period)
        self.assertEqual(len(queries), 1)
        self.assertEqual(rows[0]["image_url"], "/media/facilities/court.jpg")
        self.assertEqual(rows[0]["bookings"], 3)
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
        self.assertContains(page, 'src="/media/facilities/court.jpg"')
        self.assertNotContains(page, 'src="/media/facilities/second.jpg"')
        self.fac_court.image_url = ""
        self.fac_court.save(update_fields=["image_url"])
        self.assertEqual(most_booked_facilities(period)[0]["image_url"], "")

    def test_duplicate_names_remain_distinct_with_stable_ties(self):
        for pk in ("ranking-same-b", "ranking-same-a"):
            self.booking(Facility.objects.create(id=pk, facility_name="Same name"))
        period, _ = resolve_dashboard_period({"period": "today"}, self.today)
        self.assertEqual([row["id"] for row in most_booked_facilities(period)], ["ranking-same-a", "ranking-same-b"])

    def test_all_global_presets_and_custom_range(self):
        for day in (self.today, date(2026, 10, 1), date(2026, 9, 20), date(2026, 9, 1), date(2026, 1, 2), date(2025, 12, 31)):
            self.booking(day=day)
        for key, expected in (("today", 1), ("last_7_days", 2), ("last_30_days", 3),
                              ("this_month", 2), ("previous_month", 2), ("this_year", 5), ("custom", 2)):
            with self.subTest(period=key):
                data = self.api({"period": key, "start_date": "2026-09-01", "end_date": "2026-09-20"})
                self.assertEqual(data["facilities"]["most_booked_facilities"][0]["bookings"], expected)

    def test_chart_grouping_does_not_change_ranking(self):
        self.booking(day=self.today)
        self.booking(day=self.today - timedelta(days=3), status=Booking.STATUS_COMPLETED)
        previous = None
        for grouping in ("daily", "weekly", "monthly"):
            data = self.api({"period": "last_7_days", "booking_grouping": grouping})
            rows = data["facilities"]["most_booked_facilities"]
            self.assertEqual(rows[0]["bookings"], 2)
            if previous is not None:
                self.assertEqual(rows, previous)
            previous = rows

    def test_previous_month_year_boundary_and_full_month_comparison(self):
        period, meta = resolve_dashboard_period({"period": "previous_month"}, date(2026, 1, 6))
        self.assertEqual((period.start, period.end), (date(2025, 12, 1), date(2025, 12, 31)))
        self.assertEqual((meta["previous_start_date"], meta["previous_end_date"]), ("2025-11-01", "2025-11-30"))
        period, _ = resolve_dashboard_period({"period": "previous_month"}, date(2024, 3, 1))
        self.assertEqual(period.end, date(2024, 2, 29))

    def test_empty_populated_markup_and_export(self):
        directory = os.environ.get("MOST_BOOKED_TEST_DIR")
        for state in ("empty", "populated"):
            if state == "populated":
                for index in range(5):
                    facility = Facility.objects.create(id=f"ranking-preview-{index}", facility_name=f"Ranking Test Facility {index + 1}")
                    for count in range(index + 1):
                        self.booking(facility, status=Booking.STATUS_APPROVED if count % 2 else Booking.STATUS_COMPLETED)
            with patch("django.utils.timezone.localdate", return_value=self.today):
                page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, 'data-most-booked-facilities', count=1)
            self.assertContains(page, "Most-Booked Facilities")
            self.assertContains(page, "Facilities ranked by valid booking count")
            self.assertContains(page, "Previous Month")
            payload = self.api({"period": "today"})
            self.assertEqual(len(payload["facilities"]["most_booked_facilities"]), 5 if state == "populated" else 0)
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                (target / f"{state}.source.html").write_bytes(page.content)
                (target / f"{state}.json").write_text(json.dumps(payload), encoding="utf-8")
