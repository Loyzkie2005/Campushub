"""Collections must reconcile across the dashboard, tooltip and report."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import DatabaseError, connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts import tests as fixtures
from api.models import Booking, FacilityPayment
from modules.facilities.revenue import facility_revenue_summary
from .dashboard_periods import build_dashboard_data, resolve_dashboard_period
from .models import GeneratedReport
from .reporting import build_report


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FacilityRevenueTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 7)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        self.client.force_login(self.super_admin)
        FacilityPayment.objects.all().delete()

    def pay(self, day, amount="100.00", *, status=Booking.STATUS_APPROVED,
            payment_status=FacilityPayment.PAYMENT_PAID, paid_at=True):
        index = FacilityPayment.objects.count()
        booking = Booking.objects.create(id=f"revenue-booking-{index}", facility=self.fac_court,
            status=status, booking_date=self.today + timedelta(days=15))
        stamp = datetime.combine(day, time(12), tzinfo=ZoneInfo("Asia/Manila"))
        payment = FacilityPayment.objects.create(id=f"revenue-payment-{index}", booking=booking,
            payment_status=payment_status, paid_amount=Decimal(amount), paid_at=stamp if paid_at else None)
        FacilityPayment.objects.filter(pk=payment.pk).update(created_at=stamp - timedelta(days=90) if paid_at else stamp)
        return payment

    def data(self, params=None):
        return build_dashboard_data(params or {"period": "today"}, today=self.today)

    def test_valid_collections_exclude_invalid_statuses_missing_links_and_nonpositive_amounts(self):
        self.pay(self.today, "125.25")
        self.pay(self.today, "74.75", status=Booking.STATUS_COMPLETED)
        for status in (Booking.STATUS_PENDING, Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED):
            self.pay(self.today, "9000", status=status)
        for status in (FacilityPayment.PAYMENT_UNPAID, FacilityPayment.PAYMENT_FAILED, "pending"):
            self.pay(self.today, "9000", payment_status=status)
        self.pay(self.today, "0")
        self.pay(self.today, "-10")
        missing = self.pay(self.today, "9000")
        Booking.objects.filter(pk=missing.booking_id).update(facility=None)
        missing = self.pay(self.today, "9000")
        FacilityPayment.objects.filter(pk=missing.pk).update(booking=None)
        revenue = self.data()["facilities"]["revenue_overview"]
        self.assertEqual(revenue["total"], "200.00")
        self.assertEqual(revenue["transactions"], 2)
        self.assertEqual(revenue["chart"]["values"], [200.0])
        self.assertEqual(revenue["chart"]["transactions"], [2])
        self.assertIsNone(revenue["comparison"]["percentage_change"])
        self.assertIn("New activity", revenue["comparison"]["comparison_text"])
        # Unsupported names are not added to the actual booking workflow.
        for status in ("confirmed", "reserved"):
            self.pay(self.today, "9000", status=status)
        self.assertEqual(facility_revenue_summary(self.today, self.today)["total"], "200.00")

    def test_paid_date_fallback_and_philippine_midnight_boundaries(self):
        self.pay(self.today, "10", paid_at=False)
        before = self.pay(self.today, "9000")
        inside = self.pay(self.today, "20")
        end = self.pay(self.today, "30")
        after = self.pay(self.today, "9000")
        for payment, stamp in ((before, "2026-10-06T15:59:59+00:00"),
                               (inside, "2026-10-06T16:00:00+00:00"),
                               (end, "2026-10-07T15:59:59+00:00"),
                               (after, "2026-10-07T16:00:00+00:00")):
            FacilityPayment.objects.filter(pk=payment.pk).update(paid_at=datetime.fromisoformat(stamp))
        revenue = self.data()["facilities"]["revenue_overview"]
        self.assertEqual(revenue["total"], "60.00")
        self.assertEqual(revenue["transactions"], 3)
        report = build_report("facility_revenue", self.today, self.today)
        self.assertEqual(report["chart"]["values"], [60.0])
        self.assertEqual(len(report["rows"]), 3)
        self.assertTrue(all(row["Date"] == "Oct 07, 2026" for row in report["rows"]))

    def test_all_global_presets_and_comparisons_reconcile_with_reports(self):
        entries = [(date(2025, 10, 7), "15"), (date(2026, 8, 10), "20"),
            (date(2026, 9, 7), "30"), (date(2026, 9, 30), "40"),
            (date(2026, 10, 1), "50"), (date(2026, 10, 6), "60"), (self.today, "70")]
        for day, amount in entries:
            self.pay(day, amount)
        for preset in ("today", "last_7_days", "last_30_days", "this_month", "previous_month", "this_year", "custom"):
            params = {"period": preset, "start_date": "2026-09-30", "end_date": "2026-10-06"}
            period, meta = resolve_dashboard_period(params, self.today)
            expected = sum(Decimal(amount) for day, amount in entries if period.start <= day <= period.end)
            prior = sum(Decimal(amount) for day, amount in entries if date.fromisoformat(meta["previous_start_date"]) <= day <= date.fromisoformat(meta["previous_end_date"]))
            revenue = self.data(params)["facilities"]["revenue_overview"]
            self.assertEqual(Decimal(revenue["total"]), expected, preset)
            self.assertEqual(Decimal(revenue["previous_total"]), prior, preset)
            self.assertAlmostEqual(sum(revenue["chart"]["values"]), float(expected))
            self.assertEqual(len(revenue["chart"]["dates"]), period.days)
            self.assertEqual(revenue["start_date"], meta["start_date"])
            report = build_report("facility_revenue", period.start, period.end)
            self.assertEqual(sum(Decimal(row["Paid Amount (PHP)"]) for row in report["rows"]), expected)
        original = self.data()["facilities"]["revenue_overview"]
        for grouping in ("daily", "weekly", "monthly"):
            self.assertEqual(self.data({"period": "today", "grouping": grouping, "booking_grouping": grouping})["facilities"]["revenue_overview"], original)

    def test_previous_zero_no_change_and_current_zero_safe_comparisons(self):
        revenue = self.data()["facilities"]["revenue_overview"]
        self.assertEqual(revenue["total"], "0.00")
        self.assertEqual(revenue["chart"]["values"], [0.0])
        self.assertIn("No change", revenue["comparison"]["comparison_text"])
        self.pay(self.today - timedelta(days=1), "50")
        self.assertEqual(self.data()["facilities"]["revenue_overview"]["comparison"]["percentage_change"], -100)
        self.pay(self.today, "57")
        self.assertEqual(self.data()["facilities"]["revenue_overview"]["comparison"]["percentage_change"], 14)

    def test_one_grouped_query_and_database_failure_is_not_fake_zero(self):
        for _ in range(12):
            self.pay(self.today)
        with CaptureQueriesContext(connection) as queries:
            revenue = facility_revenue_summary(self.today, self.today,
                (self.today - timedelta(days=1), self.today - timedelta(days=1)))
        self.assertEqual(len(queries), 1)
        self.assertEqual(revenue["transactions"], 12)
        with patch("api.models.FacilityPayment.objects.filter", side_effect=DatabaseError("Unavailable")):
            with self.assertRaises(DatabaseError):
                self.data()

    def test_existing_report_route_preset_permissions_and_exports(self):
        self.pay(self.today, "120.50")
        params = {"report_type": "facility_revenue", "date_from": self.today.isoformat(), "date_to": self.today.isoformat()}
        page = self.client.get(reverse("admin_generate_reports_page"), params)
        self.assertContains(page, '<option value="facility_revenue" selected>Facility Revenue</option>', html=True)
        self.assertContains(page, 'value="2026-10-07"', count=2)
        self.assertEqual(page.context["initial_report"]["title"], "Facility Revenue")
        preview = self.client.get(reverse("admin_report_preview"), params)
        self.assertEqual(preview.json()["chart"]["values"], [120.5])
        for format in ("csv", "pdf"):
            download = self.client.get(reverse("admin_report_download"), {**params, "format": format})
            self.assertEqual(download.status_code, 200)
        self.assertEqual(GeneratedReport.objects.filter(report_type="facility_revenue").count(), 2)
        for bad in ({"date_from": "bad"}, {"date_from": "2026-10-08", "date_to": "2026-10-07"}):
            self.assertEqual(self.client.get(reverse("admin_generate_reports_page"), {**params, **bad}).status_code, 400)
        self.client.force_login(self.marketplace_admin)
        self.assertEqual(self.client.get(reverse("admin_generate_reports_page"), params).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin_report_preview"), params).status_code, 403)

    def test_card_markup_export_empty_populated_and_single_day(self):
        directory = os.environ.get("FACILITY_REVENUE_TEST_DIR")
        for state in ("empty", "populated", "single"):
            if state == "populated":
                self.pay(self.today - timedelta(days=5), "12500")
                self.pay(self.today - timedelta(days=5), "2500")
                self.pay(self.today, "750")
            params = {"period": "today" if state == "single" else "last_7_days"}
            with patch("django.utils.timezone.localdate", return_value=self.today):
                page = self.client.get(reverse("admin_facility_analytics_page"), params)
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, 'data-facility-revenue', count=1)
            self.assertNotContains(page, 'id="facilityRevenueChart"')
            self.assertContains(page, 'report_type=facility_revenue')
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                (target / f"{state}.source.html").write_text(page.content.decode(), encoding="utf-8")
                (target / f"{state}.json").write_text(json.dumps(self.data(params), default=str), encoding="utf-8")
