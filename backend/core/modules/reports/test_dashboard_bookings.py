"""Actual request dates, statuses, global filters and existing navigation."""
from datetime import date, datetime, time, timedelta
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from api.models import Booking
from .dashboard_bookings import build_booking_overview
from .dashboard_periods import build_dashboard_data, resolve_dashboard_period


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class DashboardBookingOverviewTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        Booking.objects.all().delete()
        self.client.force_login(self.super_admin)

    def booking(self, day, status=Booking.STATUS_PENDING, **fields):
        defaults = {"facility": self.fac_court, "booking_date": self.today + timedelta(days=20)}
        defaults.update(fields)
        booking = Booking.objects.create(id=f"overview-{Booking.objects.count()}", status=status, **defaults)
        with timezone.override("Asia/Manila"):
            stamp = timezone.make_aware(datetime.combine(day, time(12)))
        Booking.objects.filter(pk=booking.pk).update(created_at=stamp)
        return booking

    def payload(self, params=None):
        with patch("django.utils.timezone.localdate", return_value=self.today):
            return self.client.get(reverse("admin_dashboard_api"), params or {}).json()

    def test_five_requested_records_and_status_mapping(self):
        for status in ("pending", "pending", "approved", "completed", "cancelled"):
            self.booking(self.today, status)
        data = self.payload({"period": "today"})
        overview = data["facilities"]["booking_overview"]
        self.assertEqual({key: overview[key] for key in ("total", "pending", "approved", "completed", "rejected_cancelled")},
                         {"total": 5, "pending": 2, "approved": 1, "completed": 1, "rejected_cancelled": 1})
        self.assertEqual(overview["total"], data["kpis"]["total_bookings"]["value"])
        self.assertEqual(overview["chart"]["values"], [5])
        self.booking(self.today, "rejected")
        self.assertEqual(self.payload({"period": "today"})["facilities"]["booking_overview"]["rejected_cancelled"], 2)

    def test_creation_date_not_reservation_date_includes_undated_and_orphan_requests(self):
        self.booking(self.today - timedelta(days=60), "completed", booking_date=self.today)
        self.booking(self.today, "pending", booking_date=None, check_in_date=self.today + timedelta(days=10), check_out_date=self.today + timedelta(days=12))
        self.booking(self.today, "approved", facility=None, booking_date=None)
        overview = self.payload({"period": "today"})["facilities"]["booking_overview"]
        self.assertEqual(overview["total"], 2)
        self.assertEqual(overview["completed"], 0)
        self.assertEqual(overview["date_basis"], "created_at")

    def test_every_global_date_preset_custom_range_and_zero_baseline(self):
        for day in (self.today, self.today - timedelta(days=2), self.today - timedelta(days=10), date(2026, 1, 2), date(2025, 10, 4)):
            self.booking(day)
        for key, expected in {"today": 1, "last_7_days": 2, "last_30_days": 3, "this_month": 2, "this_year": 4, "custom": 2}.items():
            data = self.payload({"period": key, "start_date": "2026-10-01", "end_date": "2026-10-04"})
            overview = data["facilities"]["booking_overview"]
            self.assertEqual(overview["total"], expected, key)
            self.assertEqual(sum(overview["chart"]["values"]), expected, key)
            self.assertEqual(overview["start_date"], data["period"]["start_date"])
        empty = self.payload({"period": "custom", "start_date": "2026-08-01", "end_date": "2026-08-03"})["facilities"]["booking_overview"]
        self.assertEqual(empty["total"], 0)
        self.assertEqual(empty["chart"]["values"], [0, 0, 0])

    def test_selected_grouping_and_partial_buckets_preserve_all_counts(self):
        for day in (date(2026, 1, 2), date(2026, 1, 8), date(2026, 2, 1), self.today):
            self.booking(day)
        weekly = self.payload({"period": "custom", "start_date": "2026-01-02", "end_date": "2026-02-02", "booking_grouping": "weekly"})["facilities"]["booking_overview"]
        self.assertEqual(weekly["grouping"], "weekly")
        self.assertEqual(sum(weekly["chart"]["values"]), 3)
        self.assertEqual(weekly["trend"][-1]["end_date"], "2026-02-02")
        monthly = self.payload({"period": "this_year", "booking_grouping": "monthly"})["facilities"]["booking_overview"]
        self.assertEqual(monthly["grouping"], "monthly")
        self.assertEqual(sum(monthly["chart"]["values"]), 4)
        self.assertEqual(monthly["trend"][-1]["end_date"], "2026-10-04")

    def test_manila_day_boundary_and_previous_comparison(self):
        booking = self.booking(self.today)
        Booking.objects.filter(pk=booking.pk).update(created_at=datetime(2026, 10, 3, 16, 1, tzinfo=timezone.get_fixed_timezone(0)))
        data = self.payload({"period": "today"})
        self.assertEqual(data["facilities"]["booking_overview"]["total"], 1)
        self.assertIn("yesterday", data["facilities"]["booking_overview"]["comparison"]["comparison_text"])
        self.booking(self.today - timedelta(days=1))
        self.booking(self.today - timedelta(days=1))
        comparison = self.payload({"period": "today"})["facilities"]["booking_overview"]["comparison"]
        self.assertEqual(comparison["percentage_change"], -50)

    def test_one_grouped_trend_query_without_loading_booking_instances(self):
        self.booking(self.today)
        period, _ = resolve_dashboard_period({"period": "today"}, self.today)
        totals = {"current": 1, "period_pending": 1, "period_approved": 0, "period_completed": 0, "period_rejected_cancelled": 0}
        with timezone.override("Asia/Manila"), CaptureQueriesContext(connection) as queries:
            overview = build_booking_overview(period, totals, {"comparison_text": "New activity"})
        self.assertEqual(len(queries), 1)
        self.assertEqual(overview["chart"]["values"], [1])
        self.assertIn("GROUP BY", queries[0]["sql"])

    def test_existing_status_links_select_supported_booking_filters(self):
        overview = self.payload()["facilities"]["booking_overview"]
        self.assertEqual(overview["view_all_url"], reverse("admin_bookings_page"))
        for item in overview["statuses"]:
            if item["url"]:
                page = self.client.get(item["url"])
                self.assertContains(page, f'<option value="{item["key"]}" selected>')
            else:
                self.assertEqual(item["key"], "rejected_cancelled")

    def test_super_admin_endpoint_permissions_remain_enforced(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("admin_dashboard_api")).status_code, 401)
        for user in (self.marketplace_admin, self.facilities_admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("admin_dashboard_api")).status_code, 403)

    def test_actual_empty_populated_markup_and_review_artifacts(self):
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        for state in ("empty", "populated"):
            if state == "populated":
                for status in ("pending", "pending", "approved", "completed", "cancelled"):
                    self.booking(self.today, status)
            with patch("django.utils.timezone.localdate", return_value=self.today):
                page = self.client.get(reverse("admin_dashboard_page"))
            self.assertContains(page, 'data-booking-overview', count=1)
            self.assertContains(page, 'id="facilityBookingOverviewChart"', count=1)
            self.assertContains(page, 'id="bookingOverviewRetry"')
            self.assertContains(page, 'View All Bookings')
            self.assertContains(page, 'No bookings in selected period.')
            from django.template.loader import render_to_string
            markup = render_to_string('dashboard/partials/booking_overview.html', {"overview": self.payload()["facilities"]["booking_overview"]})
            self.assertNotIn('View chart data', markup)
            self.assertNotIn('<details', markup)
            self.assertNotIn('<table', markup)
            self.assertNotIn('Caution: Booking counts do not confirm facility availability.', markup)
            self.assertIn('id="bookingGroupingSelect"', markup)
            self.assertEqual(markup.count('class="booking-overview__metric-icon"'), 5)
            if directory:
                path = Path(directory)
                path.mkdir(parents=True, exist_ok=True)
                (path / f"booking-overview-{state}.html").write_bytes(page.content)
                (path / f"booking-overview-{state}.json").write_text(json.dumps(self.payload()), encoding="utf-8")

    def test_booking_grouping_is_independent_from_sales_and_global_dates(self):
        for day, status in ((date(2026, 9, 29), "approved"), (date(2026, 10, 1), "completed"), (self.today, "pending")):
            self.booking(day, status)
        for sales_grouping in ("daily", "weekly", "monthly"):
            for booking_grouping, bucket_count in (("daily", 7), ("weekly", 1), ("monthly", 2)):
                payload = self.payload({"period": "last_7_days", "grouping": sales_grouping, "booking_grouping": booking_grouping})
                overview = payload["facilities"]["booking_overview"]
                self.assertEqual(payload["grouping"], sales_grouping)
                self.assertEqual(overview["grouping"], booking_grouping)
                self.assertEqual(len(overview["trend"]), bucket_count)
                self.assertEqual(overview["total"], 3)
                self.assertEqual(sum(overview["chart"]["values"]), 3)
                self.assertEqual(overview["start_date"], "2026-09-28")
                self.assertEqual(overview["end_date"], "2026-10-04")
                for row in overview["trend"]:
                    self.assertEqual(row["count"], sum(row[key] for key in ("approved", "pending", "completed", "rejected_cancelled")))
        self.assertEqual(self.payload({"period": "this_year"})["facilities"]["booking_overview"]["grouping"], "daily")
        self.assertEqual(self.payload({"booking_grouping": "custom"})["facilities"]["booking_overview"]["grouping"], "daily")
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        if directory:
            for grouping in ("daily", "weekly", "monthly"):
                (Path(directory) / f"booking-grouping-{grouping}.json").write_text(json.dumps(self.payload({"period": "last_7_days", "grouping": "weekly", "booking_grouping": grouping})), encoding="utf-8")

    def test_one_stack_per_bucket_and_status_totals_reconcile(self):
        cases = ((date(2026, 10, 2), (3, 2, 1, 1)), (date(2026, 10, 3), (1, 1, 2, 0)), (self.today, (3, 4, 2, 1)))
        for day, counts in cases:
            for status, count in zip(("approved", "pending", "completed", "cancelled"), counts):
                for _ in range(count):
                    self.booking(day, status)
        overview = self.payload({"period": "custom", "start_date": "2026-10-02", "end_date": "2026-10-04"})["facilities"]["booking_overview"]
        self.assertEqual(overview["chart"]["values"], [7, 4, 10])
        self.assertEqual(overview["total"], 21)
        keys = ("approved", "pending", "completed", "rejected_cancelled")
        for row, (_, counts) in zip(overview["trend"], cases):
            self.assertEqual(tuple(row[key] for key in keys), counts)
            self.assertEqual(row["count"], sum(row[key] for key in keys))
            self.assertEqual(row["total"], row["count"])
        for key in keys:
            self.assertEqual(sum(overview["chart"][key]), overview[key])

    def test_all_empty_status_series_remain_zero(self):
        overview = self.payload()["facilities"]["booking_overview"]
        for key in ("approved", "pending", "completed", "rejected_cancelled"):
            self.assertEqual(overview["chart"][key], [0] * 30)

    def test_unknown_stored_status_is_not_silently_dropped(self):
        self.booking(self.today, "unsupported-workflow-state")
        with self.assertRaisesMessage(ValueError, "unsupported booking status"):
            build_dashboard_data({"period": "today"}, today=self.today)
