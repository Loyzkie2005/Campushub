from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch
import json
import os
from pathlib import Path

from django.db import DatabaseError, connection
from django.test import SimpleTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from accounts.models import User
from api.models import Booking, Facility, FacilityPayment, MarketplaceOrder, Product, Room, SellerRequest
from .dashboard_periods import build_dashboard_data, comparison_metric, resolve_dashboard_period
from .dashboard_attention import inventory_attention_counts
from .views import _aware_dashboard_datetime, _format_activity_time


@override_settings(TIME_ZONE="UTC", USE_TZ=True)
class DashboardDatetimeTests(SimpleTestCase):
    def test_legacy_naive_time_uses_default_zone_and_aware_values_are_unchanged(self):
        value = datetime(2026, 10, 13, 9)
        with timezone.override("Asia/Manila"):
            normalized = _aware_dashboard_datetime(value)
            self.assertEqual(normalized.utcoffset(), timedelta(0))
            self.assertTrue(timezone.is_naive(value), "Input is not mutated")
            self.assertIs(_aware_dashboard_datetime(normalized), normalized)
            self.assertIsNone(_aware_dashboard_datetime(None))

    def test_activity_labels_keep_today_yesterday_and_older_formats(self):
        now = timezone.make_aware(datetime(2026, 10, 13, 12), timezone.get_default_timezone())
        with timezone.override("Asia/Manila"), patch("django.utils.timezone.now", return_value=now):
            self.assertEqual(_format_activity_time(None), "")
            self.assertEqual(_format_activity_time(datetime(2026, 10, 13, 9)), "5:00 PM")
            self.assertEqual(_format_activity_time(datetime(2026, 10, 12, 9)), "Yesterday, 5:00 PM")
            self.assertEqual(_format_activity_time(datetime(2026, 10, 10, 10)), "Oct 10, 06:00 PM")
            aware = timezone.make_aware(datetime(2026, 10, 13, 9), timezone.get_default_timezone())
            self.assertEqual(_format_activity_time(aware), "5:00 PM")

    def test_mixed_activity_dates_sort_by_instant_without_type_errors(self):
        values = [datetime(2026, 10, 13, 9),
                  timezone.make_aware(datetime(2026, 10, 13, 10), timezone.get_default_timezone())]
        self.assertEqual(sorted(values, key=_aware_dashboard_datetime, reverse=True), values[::-1])


class DashboardPeriodTests(SimpleTestCase):
    def test_presets_and_equal_custom_comparison(self):
        today = date(2026, 10, 4)
        cases = {
            "today": ("2026-10-04", "2026-10-03", "2026-10-03"),
            "last_7_days": ("2026-09-28", "2026-09-21", "2026-09-27"),
            "last_30_days": ("2026-09-05", "2026-08-06", "2026-09-04"),
            "this_month": ("2026-10-01", "2026-09-01", "2026-09-04"),
            "this_year": ("2026-01-01", "2025-01-01", "2025-10-04"),
            "custom": ("2026-10-01", "2026-09-27", "2026-09-30"),
        }
        for key, expected in cases.items():
            with self.subTest(period=key):
                _, meta = resolve_dashboard_period({"period": key, "start_date": "2026-10-01", "end_date": "2026-10-04"}, today)
                self.assertEqual((meta["start_date"], meta["previous_start_date"], meta["previous_end_date"]), expected)
        self.assertEqual(resolve_dashboard_period({}, today)[1]["type"], "last_30_days")

    def test_short_month_and_leap_year_are_valid(self):
        self.assertEqual(resolve_dashboard_period({"period": "this_month"}, date(2026, 3, 31))[1]["previous_end_date"], "2026-02-28")
        self.assertEqual(resolve_dashboard_period({"period": "this_year"}, date(2024, 2, 29))[1]["previous_end_date"], "2023-02-28")

    def test_invalid_custom_dates_are_rejected(self):
        for start, end in (("", ""), ("bad", "2026-10-04"), ("2026-02-30", "2026-10-04"), ("2026-10-04", "2026-10-01"), ("2026-10-01", "2026-10-05")):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                resolve_dashboard_period({"period": "custom", "start_date": start, "end_date": end}, date(2026, 10, 4))
        with self.assertRaises(ValueError):
            resolve_dashboard_period({"period": "unsupported"})

    def test_zero_baselines_are_not_fabricated_percentages(self):
        self.assertIsNone(comparison_metric(12, 0, "previous period")["percentage_change"])
        self.assertIn("New activity", comparison_metric(12, 0, "previous period")["comparison_text"])
        self.assertEqual(comparison_metric(0, 12, "previous period")["percentage_change"], -100)
        self.assertIn("No change", comparison_metric(0, 0, "previous period")["comparison_text"])

    def test_trend_states_and_semantics(self):
        for current, previous, state, semantic, percent in ((14, 12, "up", "positive", 16.67), (11, 12, "down", "negative", -8.33), (12, 12, "unchanged", "neutral", 0), (0, 12, "down", "negative", -100), (12, 0, "new_activity", "positive", None), (0, 0, "unchanged", "neutral", None)):
            with self.subTest(current=current, previous=previous):
                result = comparison_metric(current, previous, "yesterday")
                self.assertEqual(result["trend_state"], state)
                self.assertEqual(result["semantic_type"], semantic)
                self.assertEqual(result["percentage_change"], percent)
                self.assertIn("vs yesterday", result["comparison_text"])

    def test_percentage_display_omits_unnecessary_decimals(self):
        for current, previous, expected in ((2, 1, "↑ 100%"), (14, 12, "↑ 16.7%"), (108.53, 100, "↑ 8.5%"), (50, 100, "↓ 50%"), (100.01, 100, "↑ <0.1%")):
            with self.subTest(current=current, previous=previous):
                self.assertTrue(comparison_metric(current, previous, "yesterday")["secondary_text"].startswith(expected))
        self.assertEqual(comparison_metric(2, 0, "yesterday")["secondary_text"], "↑ New activity")
        self.assertEqual(comparison_metric(0, 0, "yesterday")["secondary_text"], "— No change")


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class GlobalDashboardTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        self.client.force_login(self.super_admin)
        MarketplaceOrder.objects.all().delete()
        self.booking_upcoming.booking_date = self.today + timedelta(days=2)
        self.booking_upcoming.save(update_fields=["booking_date"])

    def stamp(self, day):
        with timezone.override("Asia/Manila"):
            return timezone.make_aware(datetime.combine(day, time(12)))

    def test_dashboard_renders_legacy_naive_booking_dates_with_aware_activities(self):
        original = Booking.from_db

        def legacy_booking(db, fields, values):
            booking = original(db, fields, values)
            value = booking.__dict__.get("created_at")
            if value and timezone.is_aware(value):
                booking.created_at = timezone.make_naive(value, timezone.get_default_timezone())
            return booking

        with patch.object(Booking, "from_db", side_effect=legacy_booking):
            response = self.client.get(reverse("admin_dashboard_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard/pages/admin_dashboard.html")
        activities = response.context["recent_activities"]
        self.assertTrue(any(item["type"] == "booking" for item in activities))
        self.assertTrue(any(timezone.is_naive(item["sort"]) for item in activities))
        self.assertTrue(any(timezone.is_aware(item["sort"]) for item in activities))
        dates = [_aware_dashboard_datetime(item["sort"]) for item in activities]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_facilities_dashboard_renders_naive_request_and_receipt_dates(self):
        Booking.objects.filter(pk=self.booking_upcoming.pk).update(status=Booking.STATUS_PENDING)
        receipt_booking = Booking.objects.create(id="legacy-receipt-approved", facility=self.fac_court,
            booking_date=self.today, start_time=time(8), end_time=time(10), status=Booking.STATUS_APPROVED)
        FacilityPayment.objects.create(id="legacy-dashboard-receipt", booking=receipt_booking,
            paid_amount=100, payment_status="paid", official_receipt_no="ISOLATED-TEST-OR", paid_at=self.stamp(self.today))
        originals = {Booking: Booking.from_db, FacilityPayment: FacilityPayment.from_db}

        def legacy_reader(model):
            def read(db, fields, values):
                instance = originals[model](db, fields, values)
                for field in ("created_at", "paid_at"):
                    value = instance.__dict__.get(field)
                    if value and timezone.is_aware(value):
                        setattr(instance, field, timezone.make_naive(value, timezone.get_default_timezone()))
                return instance
            return read

        self.client.force_login(self.facilities_admin)
        with patch.object(Booking, "from_db", side_effect=legacy_reader(Booking)), \
                patch.object(FacilityPayment, "from_db", side_effect=legacy_reader(FacilityPayment)):
            response = self.client.get(reverse("admin_dashboard_page"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "facilities/pages/admin_facilities_dashboard.html")
        self.assertTrue(response.context["facilities"]["pending_requests"][0]["date"])
        self.assertTrue(response.context["facilities"]["payment_stats"]["recent_receipts"][0]["date"])

    def order(self, day, amount="100.00", status="completed", payment="paid"):
        order = MarketplaceOrder.objects.create(
            product=self.prod_approved, product_name=self.prod_approved.name, quantity=1,
            unit_price=amount, total_price=amount, status=status, payment_status=payment,
            completed_at=self.stamp(day), paid_at=self.stamp(day),
        )
        MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=self.stamp(day))
        return order

    def api(self, params=None):
        with patch("django.utils.timezone.localdate", return_value=self.today):
            return self.client.get(reverse("admin_dashboard_api"), params or {})

    def test_all_filters_recalculate_revenue_and_preserve_snapshots(self):
        for day in (self.today, self.today - timedelta(days=2), self.today - timedelta(days=10), date(2026, 1, 2), date(2025, 10, 4)):
            self.order(day)
        expected = {"today": 100, "last_7_days": 200, "last_30_days": 300, "this_month": 200, "this_year": 400, "custom": 200}
        snapshots = None
        facility_snapshot = None
        for key, revenue in expected.items():
            payload = self.api({"period": key, "start_date": "2026-10-01", "end_date": "2026-10-04"}).json()
            self.assertEqual(payload["kpis"]["marketplace_revenue"]["value"], revenue)
            self.assertEqual(sum(payload["marketplace"]["sales_trend"]["sales"]), revenue)
            current = {key: payload["kpis"][key]["value"] for key in ("total_users", "active_sellers", "total_products", "total_facilities", "pending_approvals")}
            if snapshots is None:
                snapshots = current
            self.assertEqual(current, snapshots)
            current_facility = (payload["facilities"]["availability"], payload["facilities"]["schedule_conflicts"])
            if facility_snapshot is None:
                facility_snapshot = current_facility
            self.assertEqual(current_facility, facility_snapshot)
            self.assertTrue(payload["last_updated"].endswith("+08:00"))

    def test_revenue_requires_completed_and_paid_and_uses_completion_date(self):
        self.order(self.today, "120.00")
        for status, payment in (("pending", "paid"), ("processing", "paid"), ("ready", "unpaid"), ("cancelled", "paid"), ("completed", "unpaid")):
            self.order(self.today, "9000.00", status, payment)
        old = self.order(self.today, "80.00")
        MarketplaceOrder.objects.filter(pk=old.pk).update(created_at=self.stamp(date(2025, 1, 1)))
        payload = self.api({"period": "today"}).json()
        self.assertEqual(payload["kpis"]["marketplace_revenue"]["value"], 200)
        self.assertEqual(payload["marketplace"]["completed_orders"], 2)
        self.assertEqual(payload["marketplace"]["average_order_value"], 100)
        self.assertEqual(payload["kpis"]["total_orders"]["value"], 6)
        self.assertEqual(payload["marketplace"]["top_selling_product"]["units_sold"], 2)

    def test_comparison_bookings_paid_facilities_and_upcoming_reservations(self):
        self.order(self.today, "200.00")
        self.order(self.today - timedelta(days=1), "100.00")
        Booking.objects.filter(pk=self.booking_upcoming.pk).update(created_at=self.stamp(self.today))
        booking = Booking.objects.create(id="historical-period", facility=self.fac_court, booking_date=self.today, start_time=time(8), end_time=time(10), status="completed", total_amount=Decimal("9000"))
        Booking.objects.filter(pk=booking.pk).update(created_at=self.stamp(self.today - timedelta(days=1)))
        FacilityPayment.objects.create(id="confirmed-period", booking=booking, payment_status="paid", paid_amount=Decimal("750"), paid_at=self.stamp(self.today), official_receipt_no="OR-001")
        FacilityPayment.objects.create(id="unpaid-period", booking=booking, payment_status="unpaid", paid_amount=Decimal("9000"), paid_at=self.stamp(self.today))
        payload = self.api({"period": "today"}).json()
        self.assertEqual(payload["kpis"]["marketplace_revenue"]["percentage_change"], 100)
        self.assertEqual(payload["kpis"]["total_bookings"]["value"], 1)
        self.assertEqual(payload["kpis"]["total_bookings"]["previous_value"], 1)
        self.assertEqual(payload["facilities"]["facility_revenue"], "750.00")
        self.assertEqual(payload["facilities"]["booking_overview"]["completed"], 0)
        self.assertEqual(payload["facilities"]["booking_overview"]["total"], 1)
        self.assertEqual(payload["facilities"]["status_totals"]["completed"], 1)
        self.assertEqual(payload["facilities"]["most_booked_facility"]["name"], self.fac_court.facility_name)
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"), {"period": "custom", "start_date": "2026-09-01", "end_date": "2026-09-02"})
        self.assertContains(page, "Oct 06, 2026")
        self.assertContains(page, "No completed sales in this period.")
        self.assertNotContains(page, 'id="facilityPeriodSelect"')
        self.assertNotContains(page, 'id="salesPeriodSelect"')
        self.assertContains(page, 'id="dashboardPeriod"')

    def test_approved_student_seller_and_suspended_sellers(self):
        self.seller.role = "Student"
        self.seller.save(update_fields=["role"])
        application = SellerRequest.objects.create(user=self.seller, student_id="period-seller", full_name="Student seller", product_type="Supplies", status="approved")
        self.assertEqual(self.api().json()["kpis"]["active_sellers"]["value"], 1)
        application.is_suspended = True
        application.save(update_fields=["is_suspended"])
        self.assertEqual(self.api().json()["kpis"]["active_sellers"]["value"], 0)
        application.is_suspended = False
        application.save(update_fields=["is_suspended"])
        self.seller.is_suspended = True
        self.seller.save(update_fields=["is_suspended"])
        self.assertEqual(self.api().json()["kpis"]["active_sellers"]["value"], 0)

    def test_recorded_seller_approvals_are_distinct_and_exclude_inactive_users(self):
        for day in (self.today, self.today, self.today - timedelta(days=10)):
            SellerRequest.objects.create(user=self.seller, student_id="dated-seller", full_name="Seller", product_type="Supplies", status=SellerRequest.STATUS_APPROVED, reviewed_at=self.stamp(day))
        suspended = User.objects.create_user(username="suspended-kpi", role="Student", is_suspended=True)
        SellerRequest.objects.create(user=suspended, student_id="suspended", full_name="Suspended", product_type="Supplies", status="approved", reviewed_at=self.stamp(self.today))
        inactive = User.objects.create_user(username="inactive-kpi", role="Seller", is_active=False)
        SellerRequest.objects.create(user=inactive, student_id="inactive", full_name="Inactive", product_type="Supplies", status="approved", reviewed_at=self.stamp(self.today))
        metric = self.api({"period": "today"}).json()["kpis"]["active_sellers"]
        self.assertEqual(metric["value"], 1)
        self.assertEqual(metric["approved_in_period"], 1)
        self.assertIn("1 approval recorded", metric["secondary_text"])
        self.assertEqual(metric["semantic_type"], "neutral")
        earlier = self.api({"period": "custom", "start_date": "2026-10-01", "end_date": "2026-10-02"}).json()["kpis"]["active_sellers"]
        self.assertEqual(earlier["value"], 1)
        self.assertEqual(earlier["approved_in_period"], 0)

    def test_undated_seller_activation_has_honest_fallback(self):
        metric = self.api().json()["kpis"]["active_sellers"]
        self.assertEqual(metric["activation_dates_missing"], 1)
        self.assertEqual(metric["approved_in_period"], 0)
        self.assertEqual(metric["secondary_text"], "Current active seller access")

    def test_kpi_specific_zero_states_preserve_actual_previous_values(self):
        User.objects.all().update(date_joined=self.stamp(date(2025, 1, 1)))
        Product.objects.all().update(submitted_at=self.stamp(date(2025, 1, 1)))
        self.seller.is_active = False
        self.seller.save(update_fields=["is_active"])
        Booking.objects.filter(pk=self.booking_upcoming.pk).update(created_at=self.stamp(self.today - timedelta(days=1)))
        self.order(self.today - timedelta(days=1), "350")
        kpis = self.api({"period": "today"}).json()["kpis"]
        expected = {
            "total_users": "— 0 new in selected period",
            "active_sellers": "— No active sellers",
            "total_products": "— 0 added in selected period",
            "total_facilities": "1 open for booking",
            "total_orders": "— No orders in selected period",
            "total_bookings": "— No bookings in selected period",
            "marketplace_revenue": "— No completed sales in selected period",
            "pending_approvals": "— No pending approvals",
        }
        for key, text in expected.items():
            self.assertEqual(kpis[key]["secondary_text"], text)
            self.assertEqual(kpis[key]["semantic_type"], "neutral")
        self.assertEqual(kpis["marketplace_revenue"]["previous_value"], 350)
        self.assertEqual(kpis["marketplace_revenue"]["percentage_change"], -100)

    def test_free_completed_sales_are_not_reported_as_missing_sales(self):
        self.order(self.today, "0")
        payload = self.api({"period": "today"}).json()
        self.assertEqual(payload["marketplace"]["completed_orders"], 1)
        self.assertEqual(payload["kpis"]["marketplace_revenue"]["secondary_text"], "— No marketplace revenue in selected period")

    def test_facility_status_and_pending_breakdowns_are_current_snapshots(self):
        Facility.objects.filter(pk=self.fac_court.pk).update(availability_status=Facility.STATUS_MAINTENANCE)
        SellerRequest.objects.create(user=self.seller, student_id="pending-kpi", full_name="Pending", product_type="Supplies")
        self.prod_low.approval_status = Product.STATUS_PENDING
        self.prod_low.save(update_fields=["approval_status"])
        Booking.objects.filter(pk=self.booking_upcoming.pk).update(status=Booking.STATUS_PENDING)
        for period in ("today", "last_30_days"):
            kpis = self.api({"period": period}).json()["kpis"]
            facilities = kpis["total_facilities"]
            self.assertEqual(facilities["open"], 0)
            self.assertEqual(facilities["maintenance"], 1)
            self.assertIn("1 under maintenance", facilities["secondary_text"])
            self.assertEqual(facilities["semantic_type"], "attention")
            pending = kpis["pending_approvals"]
            self.assertEqual(pending["value"], 3)
            self.assertEqual((pending["products"], pending["sellers"], pending["bookings"]), (1, 1, 1))
            self.assertEqual(pending["semantic_type"], "attention")
            self.assertNotIn("percentage_change", pending)

    def test_accommodation_utilization_is_clipped_to_selected_days(self):
        from uuid import uuid4
        self.fac_court.facility_type = Facility.TYPE_HOSTEL
        self.fac_court.save(update_fields=['facility_type'])
        room = Room.objects.create(id=uuid4(), facility=self.fac_court, room_name='Test room')
        Booking.objects.create(
            id="hostel-period", facility=self.fac_court, room_id=room.id, status="approved",
            check_in_date=date(2026, 9, 29), check_out_date=date(2026, 10, 6),
        )
        payload = self.api({"period": "custom", "start_date": "2026-10-01", "end_date": "2026-10-04"}).json()
        facility = payload["facilities"]["utilization"][2]
        self.assertEqual(facility["used"], 4)
        self.assertEqual(facility["capacity"], 4)
        self.assertEqual(facility["percentage"], 100)

    def test_api_access_validation_and_methods(self):
        self.assertEqual(self.api({"period": "custom", "start_date": "2026-10-04", "end_date": "2026-10-01"}).status_code, 400)
        self.assertEqual(self.client.post(reverse("admin_dashboard_api")).status_code, 405)
        for user in (self.marketplace_admin, self.facilities_admin, self.seller):
            self.client.force_login(user)
            self.assertEqual(self.api().status_code, 403)
        self.client.logout()
        self.assertEqual(self.api().status_code, 401)

    def test_payment_query_failure_does_not_fabricate_revenue(self):
        with patch("api.models.FacilityPayment.objects.filter", side_effect=DatabaseError("payment table unavailable")):
            with self.assertRaises(DatabaseError):
                build_dashboard_data({"period": "today"}, today=self.today)

    def test_query_count_is_not_proportional_to_orders(self):
        with CaptureQueriesContext(connection) as before:
            build_dashboard_data({}, today=self.today)
        for index in range(20):
            self.order(self.today)
        with CaptureQueriesContext(connection) as after:
            build_dashboard_data({}, today=self.today)
        self.assertEqual(len(before), len(after))
        # Existing payload plus four bounded Users Overview aggregate queries.
        # Growing transaction data must still not add queries.
        self.assertLessEqual(len(after), 39)

    def test_philippine_midnight_boundary(self):
        from datetime import timezone as dt_timezone
        instant = datetime(2026, 10, 3, 16, 5, tzinfo=dt_timezone.utc)
        order = self.order(self.today, "75")
        MarketplaceOrder.objects.filter(pk=order.pk).update(completed_at=instant)
        with patch("django.utils.timezone.now", return_value=instant):
            payload = build_dashboard_data({"period": "today"})
        self.assertEqual(payload["period"]["start_date"], "2026-10-04")
        self.assertEqual(payload["kpis"]["marketplace_revenue"]["value"], 75)

    def test_attention_uses_current_issues_and_existing_routes(self):
        Product.objects.filter(pk=self.prod_approved.pk).update(stock=0)
        Product.objects.filter(pk=self.prod_low.pk).update(approval_status=Product.STATUS_PENDING, created_by=self.seller)
        SellerRequest.objects.create(user=self.seller, student_id="attention", full_name="Seller", product_type="Supplies")
        self.booking_upcoming.status = Booking.STATUS_PENDING
        self.booking_upcoming.save(update_fields=["status"])
        Booking.objects.create(id="attention-overlap", facility=self.fac_court, booking_date=self.booking_upcoming.booking_date,
                               start_time=time(9), end_time=time(10), status=Booking.STATUS_APPROVED)
        Facility.objects.filter(pk=self.fac_court.pk).update(availability_status=Facility.STATUS_MAINTENANCE)
        Facility.objects.create(id="attention-unavailable", facility_name="Unavailable Hall", availability_status=Facility.STATUS_UNAVAILABLE)
        current = self.api({"period": "today"}).json()["attention_required"]
        historical = self.api({"period": "custom", "start_date": "2025-01-01", "end_date": "2025-01-02"}).json()["attention_required"]
        self.assertEqual(current, historical)
        keys = ("low_stock_products", "out_of_stock_products", "pending_products", "pending_sellers", "pending_bookings",
                "booking_conflicts", "maintenance_facilities", "unavailable_facilities")
        self.assertEqual({key: current[key] for key in keys}, dict.fromkeys(keys, 1))
        expected_routes = ("/admin-products/?view=inventory&inventory_status=low_stock", "/admin-products/?view=inventory&inventory_status=out_of_stock",
                           "/admin-products/?status=pending", "/admin-sellers/?status=pending", "/admin-bookings/?status=pending",
                           "/admin-calendar/", "/admin-facility/?status=maintenance", "/admin-facility/?status=unavailable")
        self.assertEqual(tuple(item["url"] for item in current["items"]), expected_routes)
        self.assertEqual([item["key"] for item in current["items"] if item["severity"] == "serious"], ["out_of_stock_products", "booking_conflicts"])
        self.assertNotIn("backup_warnings", current)
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"))
        content = page.content.decode()
        self.assertLess(content.index('dashboard-kpi-region'), content.index('id="dashboardAttentionTitle"'))
        self.assertNotIn('id="systemStatusTitle"', content)
        for item in current["items"]:
            self.assertContains(page, f'data-attention-key="{item["key"]}"')
        self.assertNotContains(page, 'id="pendingApprovalsSlot"')
        self.assertNotContains(page, '<h2>Pending Approvals</h2>')
        self.assertContains(page, 'id="recentActivitiesTitle" tabindex="-1">Recent System Activities</h2>')
        self.assertEqual([item["action"] for item in current["items"]][2:5],
                         ["Review Products", "Review Sellers", "Review Bookings"])
        self.assertTrue(all(item["count"] > 0 for item in current["items"]))
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / "attention.html").write_bytes(page.content)
            (path / "attention-products-issues.html").write_bytes(self.client.get(reverse("admin_products_page")).content)
            (path / "payload-attention.json").write_text(json.dumps(self.api().json()), encoding="utf-8")

    def test_attention_pending_reviews_exclude_super_admin_creators_and_legacy_owners(self):
        role_admin = User.objects.create_user(username="attention-role-admin", role="Super Admin")
        for creator, owner in ((self.super_admin, self.seller), (role_admin, self.seller), (None, self.super_admin)):
            Product.objects.create(seller=owner, created_by=creator, name="Admin-created pending legacy", price=1, stock=20)
        for creator in (self.seller, None):
            Product.objects.create(seller=self.seller, created_by=creator, name="Seller review", price=1, stock=20)
        Product.objects.create(seller=self.seller, name="Archived review", price=1, stock=0, is_archived=True)
        self.assertEqual(self.api().json()["attention_required"]["pending_products"], 2)

    def test_attention_inventory_reuses_option_expiry_and_reserved_stock_rules(self):
        # Stock is already reduced at reservation; do not subtract outstanding orders again.
        from modules.marketplace.services.inventory import adjust_product_stock
        adjust_product_stock(self.prod_approved, [], 15)
        self.prod_approved.save(update_fields=["stock"])
        self.order(self.today, status="pending", payment="unpaid")
        Product.objects.filter(pk=self.prod_low.pk).update(stock=0)
        def product(name, **fields):
            return Product.objects.create(seller=self.seller, name=name, price=1, stock=20, **fields)
        product("Variant low", customization_enabled=True, customization_options=[{"options": [{"stock": 3}, {"stock": 20}]}])
        product("Variant zero", customization_options=[{"options": [{"stock": 0}, {"stock": 0}]}])
        product("No tracked options", customization_enabled=True, customization_options=[{"options": [{"name": "Size"}]}])
        expired = product("Expired simple", category=" Snacks ", expiry_date=self.today - timedelta(days=1))
        Product.objects.filter(pk=expired.pk).update(stock=0)
        product("Expired variants", category="Snacks", customization_enabled=True,
                customization_options=[{"options": [{"stock": 3, "expiry_date": "2026-10-03"}]}])
        product("Archived low", is_archived=True)
        with override_settings(CAMPUSHUB_LOW_STOCK_THRESHOLD=5):
            self.assertEqual(inventory_attention_counts(self.today), {"low_stock_products": 2, "out_of_stock_products": 2})
        with override_settings(CAMPUSHUB_LOW_STOCK_THRESHOLD=2):
            self.assertEqual(inventory_attention_counts(self.today)["low_stock_products"], 0)

    def test_attention_empty_and_archived_facilities_are_not_urgent(self):
        Product.objects.update(stock=20, approval_status=Product.STATUS_APPROVED)
        Facility.objects.create(id="archived-maintenance", facility_name="Archived", is_archived=True, availability_status=Facility.STATUS_MAINTENANCE)
        empty = self.api().json()["attention_required"]
        self.assertEqual(empty["items"], [])
        self.assertTrue(all(value == 0 for key, value in empty.items() if key != "items"))
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"))
        self.assertContains(page, 'id="dashboardAttentionEmpty">')
        self.assertContains(page, "No Items Require Attention")
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / "attention-empty.html").write_bytes(page.content)
            (path / "payload-attention-empty.json").write_text(json.dumps(self.api().json()), encoding="utf-8")

    def test_attention_conflicts_use_existing_overlap_pairs(self):
        for identifier, day, start, end, status in (
            ("touching", self.booking_upcoming.booking_date, 12, 13, "approved"),
            ("cancelled-overlap", self.booking_upcoming.booking_date, 9, 10, "cancelled"),
            ("past-overlap", self.today - timedelta(days=1), 9, 10, "approved"),
        ):
            Booking.objects.create(id=identifier, facility=self.fac_court, booking_date=day,
                                   start_time=time(start), end_time=time(end), status=status)
        self.assertEqual(self.api().json()["attention_required"]["booking_conflicts"], 0)

    def test_attention_queries_are_bounded_and_failure_is_not_all_clear(self):
        with CaptureQueriesContext(connection) as before:
            inventory_attention_counts(self.today)
        for index in range(20):
            Product.objects.create(seller=self.seller, name=f"Variant {index}", price=1,
                                   customization_options=[{"options": [{"stock": 2}]}])
        with CaptureQueriesContext(connection) as after:
            counts = inventory_attention_counts(self.today)
        self.assertEqual(len(before), 2)
        self.assertEqual(len(after), 2)
        self.assertEqual(counts["low_stock_products"], 21)
        with patch("modules.reports.dashboard_attention.inventory_attention_counts", side_effect=DatabaseError("inventory unavailable")):
            with self.assertRaises(DatabaseError):
                build_dashboard_data({}, today=self.today)

    def test_attention_destinations_preselect_supported_filters(self):
        for status in ("maintenance", "unavailable"):
            page = self.client.get(reverse("admin_facility_page"), {"status": status})
            self.assertContains(page, f'<option value="{status}" selected>')
        page = self.client.get(reverse("admin_bookings_page"), {"status": "pending"})
        self.assertContains(page, '<option value="pending" selected>')
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)
            Path(directory, "attention-products.html").write_bytes(self.client.get(reverse("admin_products_page")).content)
        SellerRequest.objects.create(user=self.seller, student_id="filter-pending", full_name="Pending Filter Seller", product_type="Supplies")
        SellerRequest.objects.create(user=self.seller, student_id="filter-approved", full_name="Approved Filter Seller", product_type="Supplies", status="approved")
        page = self.client.get(reverse("admin_sellers_page"), {"status": "pending"})
        self.assertContains(page, "Pending Filter Seller")
        self.assertNotContains(page, "Approved Filter Seller")

    def test_global_dashboard_markup_and_review_artifact(self):
        self.order(self.today, "175")
        with patch("django.utils.timezone.localdate", return_value=self.today):
            page = self.client.get(reverse("admin_dashboard_page"))
            payload = self.api({"period": "last_7_days"}).json()
            today_payload = self.api({"period": "today"}).json()
            today_page = self.client.get(reverse("admin_dashboard_page"), {"period": "today"})
        self.assertEqual(today_payload["period"]["comparison_label"], "yesterday")
        for metric in today_payload["marketplace"]["sales_overview"]["metrics"]:
            self.assertIn("vs yesterday", metric["comparison_text"])
            self.assertNotIn("previous 30", metric["comparison_text"])
        # Sales Overview keeps its full comparison; KPI new activity uses the short line.
        # Three sales metrics plus the new booking comparison and its JSON payload.
        # Facility Revenue adds a visible comparison and its initial JSON copy.
        self.assertContains(today_page, "vs yesterday", count=6)
        self.assertContains(today_page, "↑ New activity")
        self.assertNotContains(today_page, "previous 30 days")
        self.assertContains(page, "dashboardGlobalControls")
        self.assertContains(page, "dashboardLoadError")
        self.assertContains(page, "dashboardCustomRange")
        self.assertContains(page, "admin_dashboard_filter.js")
        self.assertContains(page, "admin_system_status.js")
        self.assertNotContains(page, 'id="dashboardSystemStatus"')
        self.assertNotContains(page, 'data-system-service=')
        self.assertNotContains(page, "Manage Settings")
        self.assertNotContains(page, "Connected</span>")
        # Normal dashboards must never expose the former fabricated preview data.
        for preview_marker in ("salesSampleData", "facilityUtilizationSampleData", "data-sales-sample-toggle", "Sample preview"):
            self.assertNotContains(page, preview_marker)
        directory = os.environ.get("DASHBOARD_REVIEW_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / "dashboard.html").write_bytes(page.content)
            (path / "payload.json").write_text(json.dumps(payload), encoding="utf-8")
            (path / "payload-today.json").write_text(json.dumps(today_payload), encoding="utf-8")
            # Exercise semantic updates with another real response from isolated fixtures.
            self.order(self.today - timedelta(days=1), "350")
            SellerRequest.objects.create(user=self.seller, student_id="review-approved", full_name="Approved Seller", product_type="Supplies", status="approved", reviewed_at=self.stamp(self.today))
            SellerRequest.objects.create(user=self.seller, student_id="review-pending", full_name="Pending Seller", product_type="Supplies")
            Product.objects.filter(pk=self.prod_low.pk).update(approval_status=Product.STATUS_PENDING)
            Booking.objects.filter(pk=self.booking_upcoming.pk).update(status=Booking.STATUS_PENDING)
            Facility.objects.filter(pk=self.fac_court.pk).update(availability_status=Facility.STATUS_MAINTENANCE)
            (path / "payload-decline.json").write_text(json.dumps(self.api({"period": "today"}).json()), encoding="utf-8")
