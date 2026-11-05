import json
from unittest.mock import patch
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase, TransactionTestCase, Client
from django.utils import timezone

from accounts.models import User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, FacilityPayment, FacilityBookingRequest, Room
from modules.messages.auth import mobile_chat_token


class MobileFacilityBookingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Legacy tables are unmanaged; isolated test databases need their schema.
        tables = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        suffix = uuid.uuid4().hex[:8]
        self.user = CampusHubUser.objects.create(username=f"booking-{suffix}", first_name="Test", last_name="Requestor",
            email=f"booking-{suffix}@example.edu", password_hash="unused", is_active=True)
        self.other = CampusHubUser.objects.create(username=f"other-{suffix}", first_name="Other", last_name="Requestor",
            email=f"other-{suffix}@example.edu", password_hash="unused", is_active=True)
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + mobile_chat_token(self.user)}
        self.facility = Facility.objects.create(id=f"TEST-{suffix}", facility_name="Test Court", capacity=50,
            facility_type="covered_court", booking_mode="slot", rate=Decimal("500"), price_type="hour",
            slots="08:00-12:00;13:00-17:00", availability_status="available")
        self.day = timezone.localdate() + timedelta(days=3)
        self.data = {"request_key": str(uuid.uuid4()), "facility_id": self.facility.pk,
            "date": self.day.isoformat(), "start": "13:00", "end": "17:00",
            "full_name": "Test Requestor", "organization": "Test Office", "email": "booking@example.edu",
            "contact_number": "09171234567", "event_name": "Practice", "purpose": "Sports practice",
            "attendees": 20, "additional_requirements": ["Sound System"], "notes": "Test note"}

    def post(self, path="/api/mobile/bookings/", data=None, auth=None):
        return self.client.post(path, json.dumps(self.data if data is None else data), content_type="application/json", **(self.auth if auth is None else auth))

    def test_real_request_quote_and_retry(self):
        quote = self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/")
        self.assertEqual(quote.json()["total_amount"], "2000.00")
        response = self.post(data={**self.data, "total_amount": "1", "status": "approved", "user_id": self.other.pk})
        self.assertEqual(response.status_code, 201, response.content)
        booking = Booking.objects.get(pk=response.json()["booking"]["id"])
        self.assertEqual(booking.user_id, self.user.pk)
        self.assertEqual(booking.status, "pending")
        self.assertEqual(booking.total_amount, Decimal("2000.00"))
        self.assertIn("Sound System", booking.purpose)
        self.assertEqual(self.post().status_code, 200)
        self.assertEqual(Booking.objects.filter(facility=self.facility).count(), 1)

    def test_admin_facility_status_refreshes_catalog_and_enforces_mobile_booking(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS

        self.facility.location = 'Isolated status test campus'
        self.facility.workflow_config = {'operating_hours': {
            day: {'open': '08:00', 'close': '17:00'} for day in WEEKDAYS}}
        self.facility.save()
        original_rate = self.facility.rate
        original_workflow = self.facility.workflow_config.copy()
        admin = User.objects.create_user(username='status-admin-' + uuid.uuid4().hex[:8],
                                         role='Facilities Admin', is_staff=True)
        sync_user_admin_permissions(admin)
        self.client.force_login(admin)
        for status in ('unavailable', 'maintenance', 'inactive', 'available'):
            with self.subTest(status=status):
                edited = self.client.post(f'/api/facilities/{self.facility.pk}/update/',
                    json.dumps({'status': status}), content_type='application/json')
                self.assertEqual(edited.status_code, 200, edited.content)
                self.assertEqual(edited.json()['facility']['status'], status)
                catalog = self.client.get('/api/facilities/?resource_type=facility').json()['facilities']
                self.assertEqual(next(row for row in catalog if row['id'] == self.facility.pk)['status'], status)
                self.facility.refresh_from_db()
                self.assertEqual(self.facility.availability_status, status)
                self.assertEqual(self.facility.rate, original_rate)
                self.assertEqual(self.facility.workflow_config['operating_hours'], original_workflow['operating_hours'])
                availability = self.read_availability()
                quote = self.post(f'/api/mobile/facilities/{self.facility.pk}/quote/')
                if status == 'available':
                    self.assertTrue(availability['available_slots'])
                    self.assertEqual(quote.status_code, 200, quote.content)
                else:
                    self.assertFalse(availability['available_slots'])
                    self.assertEqual(quote.status_code, 400, quote.content)
                    response = self.post()
                    self.assertEqual(response.status_code, 400, response.content)
                    self.assertFalse(Booking.objects.filter(facility=self.facility).exists())
        self.assertEqual(self.post().status_code, 201)

    def test_class_and_reservation_availability_do_not_change_catalog_facility_status(self):
        for kind in ('class', 'reservation'):
            with self.subTest(kind=kind):
                booking = Booking.objects.create(facility=self.facility, booking_date=self.day,
                    start_time=time(13), end_time=time(17), purpose=f'[{kind}] Fixture block', status='approved')
                self.assertFalse(any(row['status'] == 'available' for row in self.read_availability()['slots']
                                     if row['start'] == '13:00'))
                catalog = self.client.get('/api/facilities/?resource_type=facility').json()['facilities']
                self.assertEqual(next(row for row in catalog if row['id'] == self.facility.pk)['status'], 'available')
                self.facility.refresh_from_db()
                self.assertEqual(self.facility.availability_status, 'available')
                booking.delete()

    def test_month_uses_enabled_days_despite_stale_policy_and_refreshes_after_admin_edit(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        from api.views import _apply_facility_payload
        from modules.facilities.services.facility_configuration import validate_facility_payload
        hours = {day: {"open": "08:00", "close": "17:00"} if day in WEEKDAYS[:5] else None for day in WEEKDAYS}
        self.facility.slots = None
        self.facility.location = 'Isolated test campus'
        self.facility.workflow_config = {"operating_hours": hours, "weekend_only": True, 'allowed_booking_days': []}
        self.facility.save()
        month = (self.day.replace(day=28) + timedelta(days=4)).replace(day=1)
        path = f"/api/mobile/facilities/{self.facility.pk}/availability/?month={month:%Y-%m}"
        before = self.client.get(path, **self.auth).json()
        for day in before['days']:
            self.assertEqual(day['status'], 'available' if datetime.fromisoformat(day['date']).weekday() < 5 else 'not_bookable')
        hours['monday'] = {'open': '09:15', 'close': '16:45'}
        _apply_facility_payload(self.facility, validate_facility_payload({
            'workflow_config': {'operating_hours': hours}}, facility=self.facility))
        self.facility.save()
        response = self.client.get(path, **self.auth)
        for day in response.json()['days']:
            if datetime.fromisoformat(day['date']).weekday() == 0:
                self.assertEqual([(r['start'], r['end']) for r in day['available_slots']], [('09:15', '16:45')])
        self.assertNotIn('weekend_only', self.facility.workflow_config)
        self.assertNotIn('allowed_booking_days', self.facility.workflow_config)
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def covered_court_pricing(self, *, deposit=None):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        self.user.user_type = "student"
        self.user.save(update_fields=["user_type"])
        self.day += timedelta(days=(5 - self.day.weekday()) % 7)
        self.facility.slots = None
        self.facility.capacity = 500
        self.facility.rate = Decimal("3000")
        self.facility.price_type = "base_hour"
        self.facility.workflow_config = {
            "weekend_only": True, "minimum_booking_duration": "4", "booking_form_type": "rental",
            "operating_hours": {day: {"open": "08:00", "close": "17:00"} if day in WEEKDAYS[5:] else None for day in WEEKDAYS},
            "pricing": {"base_duration": "4", "additional_hour_rate": "500", "hourly_rate": "700"},
            "damage_deposit_applicable": deposit is not None,
            "additional_fees": [{"name": "Chairs", "unit": "item", "amount": "10", "active": True}],
            "discount_rules": [
                {"eligible_client_type": "internal", "discount_type": "percentage", "discount_value": "50", "applies_to": "entire_rental_rate", "active": True},
                {"eligible_client_type": "immediate_family", "discount_type": "percentage", "discount_value": "20", "applies_to": "entire_rental_rate", "active": True}],
        }
        if deposit is not None:
            self.facility.workflow_config["damage_deposit"] = deposit
        self.facility.save()
        self.data.update(date=str(self.day), start="08:00", end="13:00", attendees=300,
                         additional_requirements=["Chairs"], fee_quantities={"0": "20"})
        return f"/api/mobile/facilities/{self.facility.pk}/quote/"

    def test_complete_mobile_quote_matches_staff_and_persists_charge_breakdown(self):
        from modules.facilities.services.admin_reservations import reservation_quote
        url = self.covered_court_pricing()
        response = self.post(url)
        self.assertEqual(response.status_code, 200, response.content)
        quote = response.json()
        self.assertEqual([quote[key] for key in ("base_rental_amount", "additional_hour_amount", "discount_amount", "fee_amount", "deposit_amount", "total_amount")],
                         ["3000.00", "500.00", "1750.00", "200.00", "0.00", "1950.00"])
        _, staff_quote = reservation_quote(self.facility, {**self.data, "client_id": self.user.pk, "discount_index": 0, "discount_reason": "Office checked account"})
        for key in ("base_amount", "additional_hour_amount", "rental_amount", "discount_amount", "fee_amount", "deposit_amount", "total_amount"):
            self.assertEqual(quote[key], staff_quote[key], key)
        data = {**self.data, "quoted_amount": quote["total_amount"], "quote_token": quote["quote_token"]}
        created = self.post(data=data)
        self.assertEqual(created.status_code, 201, created.content)
        booking = Booking.objects.get(pk=created.json()["booking"]["id"])
        self.assertEqual((booking.status, booking.total_amount), ("pending", Decimal("1950.00")))
        self.assertEqual(booking.mobile_request.details["fee_quantities"], {"0": "20"})
        self.assertEqual(created.json()["booking"]["details"]["quote"]["fees"][0]["amount"], "200.00")
        self.assertEqual(self.post(data=data).status_code, 200)
        changed = self.post(data={**data, "purpose": "Changed after an uncertain submission"})
        self.assertEqual(changed.status_code, 409)
        self.assertEqual(Booking.objects.filter(facility=self.facility).count(), 1)
        Booking.objects.filter(pk=booking.pk).update(status="approved")
        history = self.client.get("/api/mobile/bookings/", **self.auth).json()["bookings"]
        self.assertEqual(history[0]["status"], "approved")
        self.assertEqual(history[0]["details"]["quote"]["total_amount"], "1950.00")

    def test_complete_quotes_preserve_weekend_hours_and_reject_invalid_intervals(self):
        url = self.covered_court_pricing()
        for changes in ({"date": str(self.day + timedelta(days=2))}, {"start": "07:00"}, {"end": "18:00"}, {"end": "11:00"}):
            with self.subTest(changes=changes):
                data = {**self.data, **changes}
                self.assertEqual(self.post(url, data).status_code, 400)
                self.assertEqual(self.post(data=data).status_code, 400)
        sunday = {**self.data, "date": str(self.day + timedelta(days=1))}
        self.assertEqual(self.post(url, sunday).status_code, 200)
        self.assertFalse(Booking.objects.filter(facility=self.facility).exists())

    def test_authorized_deposit_configurations_are_separate_from_chair_fees(self):
        for deposit, expected in ((None, "0.00"), ({"type": "fixed", "value": "500"}, "500.00"), ({"type": "percentage", "value": "40"}, "700.00")):
            url = self.covered_court_pricing(deposit=deposit)
            before = Facility.objects.get(pk=self.facility.pk).workflow_config
            quote = self.post(url).json()
            self.assertEqual(quote["deposit_amount"], expected)
            self.assertEqual(quote["fee_amount"], "200.00")
            self.assertEqual(Decimal(quote["total_amount"]), Decimal("1950") + Decimal(expected))
            self.assertEqual(Facility.objects.get(pk=self.facility.pk).workflow_config, before)

    def test_chair_quantity_validation_never_creates_a_booking(self):
        url = self.covered_court_pricing()
        for quantities in ({}, {"0": 0}, {"0": -1}, {"0": True}, {"0": "1.5"}, {"0": 100001}, {"5": 2}, []):
            with self.subTest(quantities=quantities):
                data = {**self.data, "fee_quantities": quantities}
                self.assertEqual(self.post(url, data).status_code, 400)
                self.assertEqual(self.post(data=data).status_code, 400)
        self.assertFalse(Booking.objects.filter(facility=self.facility).exists())

    def test_mobile_discounts_cannot_use_forged_client_or_staff_verification(self):
        url = self.covered_court_pricing()
        self.user.user_type = "guest"
        self.user.save(update_fields=["user_type"])
        quote = self.post(url).json()
        self.assertEqual((quote["discount_amount"], quote["total_amount"]), ("0.00", "3700.00"))
        for index in (0, 1):
            response = self.post(url, {**self.data, "discount_index": index, "client_id": self.other.pk,
                "client_affiliation": "internal", "discount_reason": "I say I qualify", "verification_method": "Student ID"})
            self.assertEqual(response.status_code, 400)
        self.assertFalse(Booking.objects.filter(facility=self.facility).exists())

    def test_submit_requires_review_and_revalidates_config_and_new_conflicts(self):
        url = self.covered_court_pricing()
        self.assertEqual(self.post().status_code, 400)  # A schedule-only check is not a reviewed price.
        quote = self.post(url).json()
        data = {**self.data, "quote_token": quote["quote_token"], "quoted_amount": quote["total_amount"]}
        self.facility.workflow_config["operating_hours"]["saturday"]["close"] = "16:00"
        self.facility.save(update_fields=["workflow_config"])
        self.assertEqual(self.post(data=data).status_code, 400)  # Total can match while configuration changed.
        quote = self.post(url).json()
        data.update(quote_token=quote["quote_token"])
        Booking.objects.create(id="COURT-LATE-CONFLICT", facility=self.facility, booking_date=self.day,
            start_time=time(10), end_time=time(14), status="approved", purpose="[reservation] existing")
        self.assertEqual(self.post(data=data).status_code, 400)
        self.assertEqual(Booking.objects.filter(facility=self.facility).count(), 1)

    def test_pending_conflict_and_cancel_releases_slot(self):
        response = self.post()
        booking_id = response.json()["booking"]["id"]
        collision = self.post(data={**self.data, "request_key": str(uuid.uuid4())})
        self.assertEqual(collision.status_code, 400)
        availability = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}").json()
        self.assertEqual([slot["status"] for slot in availability["slots"]], ["available", "reserved"])
        self.assertEqual(self.post(f"/api/mobile/bookings/{booking_id}/cancel/", {}).status_code, 200)
        self.assertEqual(self.post(data={**self.data, "request_key": str(uuid.uuid4())}).status_code, 201)

    def test_authorization_and_ownership(self):
        self.assertEqual(self.post(auth={}).status_code, 401)
        booking_id = self.post().json()["booking"]["id"]
        other_auth = {"HTTP_AUTHORIZATION": "Bearer " + mobile_chat_token(self.other)}
        self.assertEqual(self.client.get(f"/api/mobile/bookings/{booking_id}/", **other_auth).status_code, 404)
        self.assertEqual(self.post(f"/api/mobile/bookings/{booking_id}/cancel/", {}, other_auth).status_code, 404)
        self.assertEqual(self.client.get("/api/mobile/bookings/", **other_auth).json()["bookings"], [])

    def test_invalid_capacity_past_date_and_unconfigured_slot(self):
        for change in ({"attendees": 51}, {"attendees": 0}, {"date": "2020-01-01"}, {"start": "12:00"},
                       {"email": "bad"}, {"additional_requirements": ["Others"]}):
            with self.subTest(change=change):
                self.assertEqual(self.post(data={**self.data, **change}).status_code, 400)
        self.assertEqual(Booking.objects.filter(facility=self.facility).count(), 0)

    def test_class_and_maintenance_blocks(self):
        for event in ("class", "maintenance"):
            Booking.objects.create(id=event, facility=self.facility, booking_date=self.day,
                start_time="13:00", end_time="15:00", purpose=f"[{event}]", status="approved")
            payload = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}").json()
            self.assertEqual(payload["slots"][1]["status"], event)
            self.assertEqual(self.post().status_code, 400)
            Booking.objects.filter(id=event).delete()

    def test_approved_progress_payment_and_cancellation_rules(self):
        booking_id = self.post().json()["booking"]["id"]
        Booking.objects.filter(pk=booking_id).update(status="approved")
        self.assertTrue(self.client.get(f"/api/mobile/bookings/{booking_id}/", **self.auth).json()['booking']['can_cancel'])
        FacilityPayment.objects.create(id="PAY-TEST", booking_id=booking_id, payment_status="paid", paid_amount=2000, official_receipt_no="OR-TEST")
        response = self.client.get(f"/api/mobile/bookings/{booking_id}/", **self.auth).json()["booking"]
        self.assertTrue(response["can_view_slip"])
        self.assertEqual(response["payment_status"], "paid")
        self.assertEqual(response["receipts"][0]["number"], "OR-TEST")
        payment_before=FacilityPayment.objects.filter(booking_id=booking_id).values().get()
        result=self.post(f"/api/mobile/bookings/{booking_id}/cancel/", {})
        self.assertEqual(result.status_code,200)
        self.assertFalse(result.json()['booking']['can_cancel'])
        self.assertEqual(FacilityPayment.objects.filter(booking_id=booking_id).values().get(),payment_before)

    def test_session_rate_and_specialized_flow(self):
        self.facility.price_type = "session"
        self.facility.save()
        self.assertEqual(self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/").json()["total_amount"], "500.00")
        self.facility.booking_mode = "service"
        self.facility.facility_type = "food_analysis"
        self.facility.save()
        self.assertEqual(self.post().status_code, 400)

    def test_mobile_cancellation_reuses_start_gate_and_preserves_partial_payments(self):
        from modules.facilities.services.booking_workflow import reservation_start
        booking_id=self.post().json()['booking']['id']
        booking=Booking.objects.get(pk=booking_id)
        FacilityPayment.objects.create(id='PAY-CANCEL-PARTIAL',booking=booking,payment_status='paid',paid_amount=500,official_receipt_no='OR-PARTIAL')
        paid_before=FacilityPayment.objects.filter(booking=booking).values().get()
        start=reservation_start(booking);assert start is not None
        for status in ('pending','approved'):
            Booking.objects.filter(pk=booking_id).update(status=status)
            for instant in (start,start+timedelta(hours=6)):
                with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=instant):
                    self.assertFalse(self.client.get(f'/api/mobile/bookings/{booking_id}/',**self.auth).json()['booking']['can_cancel'])
                    response=self.post(f'/api/mobile/bookings/{booking_id}/cancel/',{})
                    self.assertEqual(response.status_code,409)
                    self.assertIn('already started',response.json()['error'])
        with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=start-timedelta(seconds=1)):
            self.assertTrue(self.client.get(f'/api/mobile/bookings/{booking_id}/',**self.auth).json()['booking']['can_cancel'])
            self.assertEqual(self.post(f'/api/mobile/bookings/{booking_id}/cancel/',{}).status_code,200)
        self.assertEqual(FacilityPayment.objects.filter(booking=booking).values().get(),paid_before)
        booking.refresh_from_db()
        saved_cancel=booking.mobile_request.details['cancel']
        self.assertEqual(saved_cancel['by']['id'],booking.user_id)
        self.assertTrue(saved_cancel['by']['name'])
        self.assertTrue(saved_cancel['at'])
        self.assertNotIn('reason',saved_cancel)  # The mobile form did not collect one.
        self.assertEqual(self.post(f'/api/mobile/bookings/{booking_id}/cancel/',{}).status_code,409)

    def test_admin_cannot_create_overlapping_schedule(self):
        self.post()
        admin = User.objects.create_user(username="booking-admin-" + uuid.uuid4().hex[:8], role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(admin)
        self.client.force_login(admin)
        response = self.client.post("/api/bookings/create/", json.dumps({"facility_id": self.facility.pk,
            "date": self.day.isoformat(), "start": "14:00", "end": "16:00", "type": "class", "purpose": "Academic class"}), content_type="application/json")
        self.assertEqual(response.status_code, 409, response.content)

    def test_weekly_hours_enforced_on_availability_quote_and_submit(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS

        hours = {day: {"open": "08:00", "close": "17:00"} for day in WEEKDAYS}
        hours[WEEKDAYS[self.day.weekday()]] = None
        self.facility.workflow_config = {"operating_hours": hours}
        self.facility.save()
        path = f"/api/mobile/facilities/{self.facility.pk}"
        self.assertEqual(self.client.get(f"{path}/availability/?date={self.day}").json()["slots"], [])
        self.assertEqual(self.post(f"{path}/quote/").status_code, 400)
        self.assertEqual(self.post().status_code, 400)
        self.facility.refresh_from_db()
        self.assertEqual(self.facility.availability_status, "available")
        self.assertFalse(Booking.objects.filter(facility=self.facility).exists())

    def test_minimum_duration_does_not_offer_invalid_daily_window(self):
        self.facility.slots = None
        self.facility.workflow_config = {"operating_hours": "13:00-17:00", "minimum_booking_duration": "6 hours"}
        self.facility.save()
        path = f"/api/mobile/facilities/{self.facility.pk}"
        self.assertEqual(self.client.get(f"{path}/availability/?date={self.day}").json()["slots"][0]["status"], "unavailable")
        self.assertEqual(self.post(f"{path}/quote/").status_code, 400)
        self.assertEqual(self.post().status_code, 400)

    def test_predefined_slot_duration_and_blocked_reservations(self):
        self.facility.workflow_config = {"minimum_booking_duration": "20 hours"}
        self.facility.save()
        path = f"/api/mobile/facilities/{self.facility.pk}"
        self.assertEqual(self.post(f"{path}/quote/").status_code, 200)
        for purpose in ("[reservation]", "[blocked]", "[assessment]"):
            booking = Booking.objects.create(id=f"BLOCK-{uuid.uuid4().hex[:12]}", facility=self.facility,
                booking_date=self.day, start_time="13:00", end_time="17:00", purpose=purpose, status="approved")
            expected = "reserved" if purpose == "[reservation]" else "blocked"
            self.assertEqual(self.client.get(f"{path}/availability/?date={self.day}").json()["slots"][1]["status"], expected)
            self.assertEqual(self.post().status_code, 400)
            booking.delete()

    def admin_schedule(self, **changes):
        admin = User.objects.create_user(username="availability-admin-" + uuid.uuid4().hex[:8], role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(admin)
        self.client.force_login(admin)
        data = {"facility_id": self.facility.pk, "type": "class", "purpose": "Private admin title",
                "date": str(self.day), "start": "08:00", "end": "12:00", **changes}
        response = self.client.post("/api/bookings/create/", json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()["event"]["id"], data

    def read_availability(self, day=None, **query):
        response = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/",
                                   query or {"date": str(day or self.day)}, **self.auth)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertNotIn("Private admin title", response.content.decode())
        return response.json()

    def test_admin_all_day_maintenance_and_every_block_type_reach_mobile(self):
        self.custom_hours()
        for kind, state in (("maintenance", "maintenance"), ("class", "class"), ("official", "blocked"), ("hold", "blocked"), ("other", "blocked")):
            with self.subTest(kind=kind):
                pk, _ = self.admin_schedule(type=kind, all_day=True, other_type="Campus activity")
                result = self.read_availability()
                self.assertEqual(result["status"], state)
                self.assertEqual(result["available_slots"], [])
                self.assertEqual(result["slots"][0]["blocking_types"], [kind])
                self.assertEqual(self.post().status_code, 400)
                Booking.objects.filter(pk=pk).delete()  # Isolated test DB only.

    def test_admin_partial_blocks_preserve_valid_custom_and_preset_periods(self):
        self.custom_hours()
        for kind in ("class", "official", "hold", "other"):
            pk, _ = self.admin_schedule(type=kind, other_type="Timed activity")
            result = self.read_availability()
            self.assertEqual(result["status"], "available")
            self.assertEqual([(r["start"], r["end"]) for r in result["available_slots"]], [("12:00", "17:00")])
            blocked = {**self.data, "start": "10:00", "end": "14:00", "availability_only": True}
            self.assertEqual(self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/", blocked).status_code, 400)
            Booking.objects.filter(pk=pk).delete()
        self.facility.slots = "08:00-10:00;10:00-12:00;13:00-17:00"
        self.facility.save()
        self.admin_schedule(start="09:00", end="11:00")
        self.assertEqual([r["start"] for r in self.read_availability()["available_slots"]], ["13:00"])

    def test_admin_edit_cancel_and_delete_are_visible_on_next_read(self):
        self.custom_hours()
        pk, data = self.admin_schedule(type="official", all_day=True)
        self.assertEqual(self.read_availability()["status"], "blocked")
        response = self.client.post(f"/api/facility-schedules/{pk}/update/",
            json.dumps({**data, "all_day": False, "start": "08:00", "end": "10:00"}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.read_availability()["available_slots"][0]["start"], "10:00")
        response = self.client.post(f"/api/facility-schedules/{pk}/update/", json.dumps({"action": "cancel"}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.read_availability()["available_slots"][0]["start"], "08:00")
        Booking.objects.filter(pk=pk).delete()
        self.assertEqual(self.read_availability()["slots"][0]["status"], "available")

    def test_month_policy_past_dates_and_manila_midnight(self):
        self.custom_hours()
        self.facility.workflow_config["weekend_only"] = True
        self.facility.save()
        saturday = self.day + timedelta(days=(5 - self.day.weekday()) % 7)
        monday = saturday + timedelta(days=2)
        self.assertEqual(self.read_availability(saturday)["status"], "available")
        result = self.read_availability(monday)
        self.assertEqual(result["status"], "available")
        self.assertEqual(self.read_availability(timezone.localdate() - timedelta(days=1))["status"], "not_bookable")
        month = self.read_availability(month=self.day.strftime("%Y-%m"))
        self.assertEqual(month["timezone"], "Asia/Manila")
        for row in month["days"]:
            self.assertEqual(row, self.read_availability(row["date"]))
        from zoneinfo import ZoneInfo
        instant = datetime(2026, 11, 6, 16, 30, tzinfo=ZoneInfo("UTC"))
        with patch("modules.facilities.services.mobile_booking.timezone.localtime", return_value=instant.astimezone(ZoneInfo("Asia/Manila"))):
            self.assertEqual(self.read_availability(datetime(2026, 11, 6).date())["status"], "not_bookable")
            self.assertEqual(self.read_availability(datetime(2026, 11, 7).date())["status"], "available")
        for value in ("bad", "2026-13", "9999-12"):
            self.assertEqual(self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/", {"month": value}).status_code, 400)

    def test_recurring_admin_schedule_effective_range_facility_and_reservations(self):
        self.custom_hours()
        until = self.day + timedelta(days=14)
        pk, _ = self.admin_schedule(type="maintenance", all_day=True, until=str(until), repeat="weekly", weekdays=[self.day.weekday()])
        for offset in (0, 7, 14):
            self.assertEqual(self.read_availability(self.day + timedelta(days=offset))["status"], "maintenance")
        for offset in (-1, 1, 15, 21):
            self.assertEqual(self.read_availability(self.day + timedelta(days=offset))["status"], "available")
        self.assertEqual(Booking.objects.filter(pk=pk).count(), 1)
        other = Facility.objects.create(id="OTHER-" + uuid.uuid4().hex[:8], facility_name="Other Court", booking_mode="slot", slots="08:00-17:00")
        Booking.objects.filter(pk=pk).update(facility=other)
        self.assertEqual(self.read_availability()["status"], "available")
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.post(data={**self.data, "request_key": str(uuid.uuid4())}).status_code, 400)
        self.assertEqual(self.read_availability()["slots"][-1]["status"], "reserved")

    def test_overlapping_blocks_metadata_precedence_and_ineligible_clients(self):
        self.custom_hours()
        # Legacy overlapping records must produce stable categories, not DB-order dependent ones.
        for kind, start, end in (("class", "08:00", "12:00"), ("maintenance", "10:00", "14:00"), ("hold", "14:00", "17:00")):
            record = Booking.objects.create(id="OVERLAP-" + uuid.uuid4().hex[:8], facility=self.facility, booking_date=self.day,
                start_time=start, end_time=end, status="approved", purpose="Legacy title")
            FacilityBookingRequest.objects.create(booking=record, request_key=uuid.uuid4(), details={"source": "schedule", "schedule": {
                "type": kind, "until": str(self.day), "repeat": "none", "all_day": False}})
        result = self.read_availability()
        self.assertEqual(result["available_slots"], [])
        self.assertEqual([r["status"] for r in result["slots"]], ["class", "maintenance", "maintenance", "blocked"])
        self.assertEqual(result["status"], "maintenance")
        self.facility.workflow_config["eligible_clients"] = "external"
        self.facility.save()
        self.assertEqual(self.read_availability()["status"], "not_bookable")
        self.assertEqual(self.read_availability()["available_slots"], [])

    def custom_hours(self):
        self.facility.slots = None
        self.facility.workflow_config = {"operating_hours": "08:00-17:00"}
        self.facility.save(update_fields=["slots", "workflow_config"])

    def test_custom_availability_preserves_free_time_around_a_real_class(self):
        self.custom_hours()
        Booking.objects.create(id="PARITY-CLASS", facility=self.facility, booking_date=self.day,
            start_time=time(9), end_time=time(10), purpose="[class] Private class title", status="approved")
        rows = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}").json()["slots"]
        self.assertEqual([(r["start"], r["end"], r["status"]) for r in rows],
            [("08:00", "09:00", "available"), ("09:00", "10:00", "class"), ("10:00", "17:00", "available")])
        self.assertTrue(all(r["time_selection"] == "custom" for r in rows))
        self.assertNotIn("Private class title", json.dumps(rows))
        self.assertEqual(Booking.objects.filter(facility=self.facility).count(), 1)
        self.facility.workflow_config["minimum_booking_duration"] = "4"
        self.facility.save(update_fields=["workflow_config"])
        rows = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}").json()["slots"]
        self.assertEqual([row["status"] for row in rows], ["unavailable", "class", "available"])

    def test_partial_recurring_class_lifecycle_preserves_minimum_and_approved_reservations(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        self.day += timedelta(days=(5 - self.day.weekday()) % 7)
        for category in ('covered_court', 'function_hall', 'hostel', 'other'):
            with self.subTest(category=category):
                self.facility.facility_type = category
                self.facility.slots = ''
                self.facility.workflow_config = {'operating_hours': self.daily_hours(),
                    'minimum_booking_duration': '4', 'weekend_only': category == 'covered_court'}
                self.facility.save(update_fields=['facility_type', 'slots', 'workflow_config'])
                self.assertEqual([(r['start'], r['end']) for r in self.read_availability()['available_slots']], [('08:00', '17:00')])
                until = self.day + timedelta(days=14)
                key, config = self.admin_schedule(start='10:00', end='13:00', repeat='weekly',
                    weekdays=[self.day.weekday()], until=str(until))
                for offset in (0, 7, 14):
                    result = self.read_availability(self.day + timedelta(days=offset))
                    self.assertEqual([(r['start'], r['end'], r['status']) for r in result['slots']],
                        [('08:00', '10:00', 'unavailable'), ('10:00', '13:00', 'class'), ('13:00', '17:00', 'available')])
                    self.assertEqual(result['slots'][1]['reason'], 'Class / Academic Schedule')
                    self.assertEqual(result['available_slots'][0]['minimum_duration_minutes'], 240)
                for offset in (1, 21):
                    self.assertEqual(len(self.read_availability(self.day + timedelta(days=offset))['available_slots']), 1)
                monday = self.day + timedelta(days=2)
                self.assertEqual(self.read_availability(monday)['status'], 'available')
                quote_path = f'/api/mobile/facilities/{self.facility.pk}/quote/'
                self.assertEqual(self.post(quote_path, {'date': str(self.day), 'start': '08:00', 'end': '10:00', 'availability_only': True}).status_code, 400)
                self.assertEqual(self.facility.bookings.count(), 1)
                conflict = self.client.post('/api/bookings/create/', json.dumps({**config,
                    'type': 'official', 'start': '11:00', 'end': '12:00'}), content_type='application/json')
                self.assertEqual(conflict.status_code, 409, conflict.content)
                approved = Booking.objects.create(id='KEEP-APPROVED-' + uuid.uuid4().hex[:8], facility=self.facility,
                    booking_date=self.day + timedelta(days=7), start_time='13:00', end_time='17:00', status='approved')
                update_path = f'/api/facility-schedules/{key}/update/'
                conflict = self.client.post(update_path, json.dumps({**config, 'end': '14:00'}), content_type='application/json')
                self.assertEqual(conflict.status_code, 409, conflict.content)
                block = Booking.objects.get(pk=key)
                self.assertEqual(block.end_time, time(13))
                self.assertEqual(self.facility.bookings.count(), 2)
                edited = self.client.post(update_path, json.dumps({**config, 'start': '09:00', 'end': '12:00'}), content_type='application/json')
                self.assertEqual(edited.status_code, 200, edited.content)
                self.assertEqual([(r['start'], r['end']) for r in self.read_availability()['available_slots']], [('12:00', '17:00')])
                cancelled = self.client.post(update_path, json.dumps({'action': 'cancel'}), content_type='application/json')
                self.assertEqual(cancelled.status_code, 200, cancelled.content)
                self.assertEqual([(r['start'], r['end']) for r in self.read_availability()['available_slots']], [('08:00', '17:00')])
                later = self.read_availability(self.day + timedelta(days=7))
                self.assertEqual([(r['start'], r['end']) for r in later['available_slots']], [('08:00', '13:00')])
                self.assertEqual(later['slots'][-1]['status'], 'reserved')
                approved.refresh_from_db()
                self.assertEqual(approved.status, 'approved')
                self.assertEqual(FacilityPayment.objects.filter(booking__facility=self.facility).count(), 0)
                self.facility.bookings.all().delete()  # Isolated fixture cleanup between categories only.

    def test_mobile_custom_times_match_web_validation_and_persist_exact_choice(self):
        from modules.facilities.services.admin_reservations import reservation_schedule
        self.custom_hours()
        data = {**self.data, "start": "13:00", "end": "15:00"}
        fields, context = reservation_schedule(self.facility, data, check_capacity=False)
        self.assertEqual(context["hours"], Decimal("2"))
        quote = self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/", data)
        self.assertEqual(quote.status_code, 200, quote.content)
        self.assertEqual(quote.json()["total_amount"], "1000.00")
        response = self.post(data=data)
        self.assertEqual(response.status_code, 201, response.content)
        booking = Booking.objects.get(pk=response.json()["booking"]["id"])
        self.assertEqual((booking.start_time, booking.end_time), (fields["start_time"], fields["end_time"]))
        self.assertEqual(booking.user_id, self.user.pk)
        self.assertEqual(booking.status, "pending")

    def test_custom_schedule_rejects_new_conflicts_and_too_short_choices(self):
        from django.core.exceptions import ValidationError
        from modules.facilities.services.admin_reservations import reservation_schedule
        self.custom_hours()
        self.facility.workflow_config["minimum_booking_duration"] = "2"
        self.facility.save(update_fields=["workflow_config"])
        rows = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}").json()["slots"]
        self.assertTrue(all(row["minimum_duration_minutes"] == 120 for row in rows))
        data = {**self.data, "start": "13:00", "end": "14:00"}
        with self.assertRaises(ValidationError):
            reservation_schedule(self.facility, data, check_capacity=False)
        self.assertEqual(self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/", data).status_code, 400)
        data["end"] = "15:00"
        self.assertEqual(self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/", data).status_code, 200)
        Booking.objects.create(id="PARITY-NEW-CONFLICT", facility=self.facility, booking_date=self.day,
            start_time=time(14), end_time=time(16), purpose="[reservation] Other request", status="pending")
        with self.assertRaises(ValidationError):
            reservation_schedule(self.facility, data, check_capacity=False)
        self.assertEqual(self.post(data=data).status_code, 400)
        self.assertEqual(Booking.objects.filter(facility=self.facility).count(), 1)

    def test_preset_slots_do_not_become_custom_time_ranges(self):
        rows = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}").json()["slots"]
        self.assertTrue(all("time_selection" not in row for row in rows))
        self.assertEqual(self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/",
            {**self.data, "start": "13:00", "end": "15:00"}).status_code, 400)

    def test_schedule_only_check_does_not_bypass_full_pricing_or_submission(self):
        self.custom_hours()
        self.facility.workflow_config["damage_deposit_applicable"] = True
        self.facility.save(update_fields=["workflow_config"])
        data = {**self.data, "start": "10:00", "end": "14:00"}
        url = f"/api/mobile/facilities/{self.facility.pk}/quote/"
        available = self.post(url, {**data, "availability_only": True})
        self.assertEqual(available.status_code, 200, available.content)
        self.assertEqual(available.json(), {"available": True, "date": self.day.isoformat(), "start": "10:00", "end": "14:00",
                                            "pricing_options": {"item_fees": []}})
        self.assertNotIn("total_amount", available.json())
        self.assertEqual(self.post(url, data).status_code, 400)
        self.assertEqual(self.post(data={**data, "availability_only": True}).status_code, 400)
        self.assertFalse(Booking.objects.filter(facility=self.facility).exists())
        self.assertEqual(self.client.post(url, json.dumps({**data, "availability_only": True}), content_type="application/json").status_code, 401)
        self.facility.workflow_config["minimum_booking_duration"] = "6"
        self.facility.save(update_fields=["workflow_config"])
        self.assertEqual(self.post(url, {**data, "availability_only": True}).status_code, 400)

    def test_custom_availability_uses_real_recurring_and_all_day_blocks(self):
        self.custom_hours()
        booking = Booking.objects.create(id="PARITY-RECURRING", facility=self.facility, booking_date=self.day,
            start_time=time(9), end_time=time(10), purpose="[class] Weekly class", status="approved")
        FacilityBookingRequest.objects.create(booking=booking, request_key=uuid.uuid4(), details={
            "source": "schedule", "schedule": {"type": "class", "repeat": "weekly",
                "weekdays": [self.day.weekday()], "until": (self.day + timedelta(days=14)).isoformat(), "all_day": False}})
        target = self.day + timedelta(days=7)
        rows = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={target}").json()["slots"]
        self.assertEqual([r["status"] for r in rows], ["available", "class", "available"])
        Booking.objects.create(id="PARITY-ALL-DAY", facility=self.facility, booking_date=target,
            start_time=time.min, end_time=time(23, 59, 59), purpose="[maintenance] All day", status="approved")
        rows = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={target}").json()["slots"]
        self.assertTrue(all(r["status"] == "maintenance" for r in rows))

    def test_custom_today_keeps_future_time_after_elapsed_opening(self):
        self.custom_hours()
        today = timezone.localdate()
        now = timezone.make_aware(datetime.combine(today, time(12, 30, 20)))
        with patch("modules.facilities.services.mobile_booking.timezone.localtime", return_value=now):
            rows = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={today}").json()["slots"]
        self.assertEqual([(r["start"], r["end"], r["status"]) for r in rows],
            [("08:00", "12:31", "unavailable"), ("12:31", "17:00", "available")])

    def test_admin_api_round_trip_and_invalid_schedule(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS

        admin = User.objects.create_user(username="form-admin-" + uuid.uuid4().hex[:8], role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(admin)
        self.client.force_login(admin)
        hours = {day: {"open": "08:00", "close": "17:00"} if day in WEEKDAYS[:5] else None for day in WEEKDAYS}
        payload = {"name": "Test Form Facility", "facility_type": "covered_court", "location": "Test Campus",
                   "capacity": 50, "rate": "500", "mode": "slot", "price_type": "hour",
                   "amenities": ["Lighting", "Custom | amenity"], "workflow_config": {"operating_hours": hours}}
        response = self.client.post('/api/facilities/create/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 201, response.content)
        data = response.json()["facility"]
        saved = Facility.objects.get(pk=data["id"])
        self.assertEqual(saved.workflow_config["operating_hours"], hours)
        self.assertEqual(saved.amenities, payload["amenities"])
        saved.slots = "08:00-12:00;13:00-17:00"
        saved.save()
        payload['workflow_config']['minimum_booking_duration'] = '24'
        response = self.client.post(f'/api/facilities/{saved.pk}/update/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn('minimum_booking_duration', response.json()['facility']['workflow_config'])
        payload['workflow_config']['operating_hours']['monday']['close'] = '07:00'
        response = self.client.post(f'/api/facilities/{saved.pk}/update/', json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        saved.refresh_from_db()
        self.assertEqual(saved.workflow_config['operating_hours']['monday']['close'], '17:00')

    def schedule_update(self, hours, **workflow):
        admin = User.objects.create_user(username="schedule-admin-" + uuid.uuid4().hex[:8], role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(admin)
        self.client.force_login(admin)
        return self.client.post(f'/api/facilities/{self.facility.pk}/update/',
            json.dumps({"location": "Test Campus", "workflow_config": {"operating_hours": hours, **workflow}}), content_type='application/json')

    def daily_hours(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        return {day: {"open": "08:00", "close": "17:00"} for day in WEEKDAYS}

    def test_schedule_update_protects_active_reservations_without_writes(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        from accounts.models import AccountActivity
        hours = self.daily_hours()
        self.facility.workflow_config = {"operating_hours": hours}
        self.facility.save(update_fields=['workflow_config'])
        day = WEEKDAYS[self.day.weekday()]
        for status in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED):
            booking = Booking.objects.create(id='PROTECT-' + status, facility=self.facility,
                booking_date=self.day, start_time='13:00', end_time='17:00', status=status)
            for replacement in (None, {"open": "14:00", "close": "17:00"}, {"open": "08:00", "close": "16:00"}):
                with self.subTest(status=status, replacement=replacement):
                    before = AccountActivity.objects.count()
                    response = self.schedule_update({**hours, day: replacement})
                    self.assertEqual(response.status_code, 400, response.content)
                    self.assertIn('operating_hours', response.json()['errors'])
                    self.facility.refresh_from_db()
                    self.assertEqual(self.facility.workflow_config['operating_hours'], hours)
                    self.assertEqual(AccountActivity.objects.count(), before)
                    booking.refresh_from_db()
                    self.assertEqual(booking.status, status)
            booking.delete()

    def test_schedule_update_can_expand_or_change_an_unrelated_day(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        hours = self.daily_hours()
        self.facility.workflow_config = {"operating_hours": hours}
        self.facility.save(update_fields=['workflow_config'])
        Booking.objects.create(id='PROTECT-EXPAND', facility=self.facility, booking_date=self.day,
            start_time='13:00', end_time='17:00', status=Booking.STATUS_APPROVED)
        day = WEEKDAYS[self.day.weekday()]
        expanded = {**hours, day: {"open": "07:00", "close": "18:00"}}
        self.assertEqual(self.schedule_update(expanded).status_code, 200)
        other_day = WEEKDAYS[(self.day.weekday() + 1) % 7]
        self.assertEqual(self.schedule_update({**expanded, other_day: None}).status_code, 200)

    def test_schedule_update_preserves_calendar_blocks_and_ignores_inactive_reservations(self):
        from datetime import timedelta
        from modules.facilities.services.operating_schedule import WEEKDAYS
        hours = self.daily_hours()
        self.facility.workflow_config = {"operating_hours": hours}
        self.facility.save(update_fields=['workflow_config'])
        for status in (Booking.STATUS_CANCELLED, Booking.STATUS_REJECTED, Booking.STATUS_COMPLETED):
            Booking.objects.create(id='IGNORE-' + status, facility=self.facility, booking_date=self.day,
                start_time='13:00', end_time='17:00', status=status)
        Booking.objects.create(id='IGNORE-PAST', facility=self.facility, booking_date=timezone.localdate() - timedelta(days=1),
            start_time='13:00', end_time='17:00', status=Booking.STATUS_APPROVED)
        for kind in ('Maintenance', 'Class', 'Official', 'Hold'):
            Booking.objects.create(id='KEEP-' + kind, facility=self.facility, booking_date=self.day,
                start_time='13:00', end_time='17:00', status=Booking.STATUS_APPROVED, purpose=f'[{kind}] Test block')
        count = self.facility.bookings.count()
        closed = {**hours, WEEKDAYS[self.day.weekday()]: None}
        self.assertEqual(self.schedule_update(closed).status_code, 200)
        self.assertEqual(self.facility.bookings.count(), count)

    def test_saved_schedule_reaches_public_catalog_and_mobile_availability(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        hours = {day: None for day in WEEKDAYS}
        day = WEEKDAYS[self.day.weekday()]
        hours[day] = {"open": "13:00", "close": "17:00"}
        response = self.schedule_update(hours)
        self.assertEqual(response.status_code, 200, response.content)
        catalog = self.client.get('/api/facilities/').json()['facilities']
        data = next(item for item in catalog if item['id'] == self.facility.pk)
        self.assertEqual(data['workflow_config']['operating_hours'], hours)
        path = f'/api/mobile/facilities/{self.facility.pk}/availability/'
        slots = self.client.get(f'{path}?date={self.day}').json()['slots']
        self.assertEqual([(slot['start'], slot['end']) for slot in slots], [('13:00', '17:00')])
        self.assertEqual(self.client.get(f'{path}?date={self.day + timedelta(days=1)}').json()['slots'], [])

    def test_schedule_update_replaces_retired_policy_with_enabled_operating_days(self):
        self.facility.workflow_config = {'weekend_only': True, 'allowed_booking_days': [], 'operating_hours': self.daily_hours()}
        self.facility.save(update_fields=['workflow_config'])
        response = self.schedule_update(self.daily_hours(), weekend_only=True, allowed_booking_days=[])
        self.assertEqual(response.status_code, 200, response.content)
        self.facility.refresh_from_db()
        self.assertNotIn('weekend_only', self.facility.workflow_config)
        self.assertNotIn('allowed_booking_days', self.facility.workflow_config)

    def test_all_weekly_categories_follow_saved_hours_and_protect_reservations(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        from modules.facilities.services.admin_reservations import reservation_schedule
        from django.core.exceptions import ValidationError

        day = WEEKDAYS[self.day.weekday()]
        for category in ('covered_court', 'function_hall', 'hostel', 'other'):
            with self.subTest(category=category):
                self.facility.facility_type = category
                self.facility.slots = ''
                self.facility.workflow_config = {'operating_hours': self.daily_hours(),
                    'custom_facility_type': 'Isolated test space', 'booking_form_type': 'general'}
                self.facility.save(update_fields=['facility_type', 'slots', 'workflow_config'])
                revised = {day: None for day in WEEKDAYS}
                revised[day] = {'open': '09:15', 'close': '16:45'}
                result = self.schedule_update(revised)
                self.assertEqual(result.status_code, 200, result.content)
                self.facility.refresh_from_db()
                self.assertEqual(self.facility.workflow_config['operating_hours'], revised)
                path = f'/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}'
                slots = self.client.get(path, **self.auth).json()['slots']
                self.assertEqual([(row['start'], row['end']) for row in slots], [('09:15', '16:45')])
                with self.assertRaises(ValidationError):
                    reservation_schedule(self.facility, {'date': str(self.day), 'start': '08:00', 'end': '12:00'}, check_capacity=False)
                for status in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED):
                    booking = Booking.objects.create(id='ALL-' + uuid.uuid4().hex[:12], facility=self.facility,
                        booking_date=self.day, start_time='13:00', end_time='16:00', status=status)
                    blocked = self.schedule_update({**revised, day: {'open': '09:15', 'close': '15:00'}})
                    self.assertEqual(blocked.status_code, 400, blocked.content)
                    self.facility.refresh_from_db()
                    self.assertEqual(self.facility.workflow_config['operating_hours'], revised)
                    booking.refresh_from_db()
                    self.assertEqual(booking.status, status)
                    booking.delete()

    def test_enabled_weekday_hours_allow_quote_and_submission_despite_legacy_policy(self):
        self.facility.slots = ''
        self.facility.workflow_config = {'weekend_only': True, 'operating_hours': self.daily_hours(),
            'allowed_booking_days': [], 'minimum_booking_duration': '4'}
        self.facility.save(update_fields=['slots', 'workflow_config'])
        monday = self.day + timedelta(days=(0 - self.day.weekday()) % 7 or 7)
        path = f'/api/mobile/facilities/{self.facility.pk}/'
        weekday = self.client.get(f'{path}availability/?date={monday}').json()
        self.assertEqual(weekday['status'], 'available')
        self.assertTrue(weekday['available_slots'])
        self.data.update(date=str(monday))
        quote = self.post(path + 'quote/', self.data)
        self.assertEqual(quote.status_code, 200, quote.content)
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.facility.bookings.count(), 1)

    def test_operating_edits_remove_hidden_rules_and_preserve_active_reservations(self):
        from modules.facilities.services.operating_schedule import WEEKDAYS
        self.facility.facility_type = 'function_hall'
        self.facility.slots = ''
        day = WEEKDAYS[self.day.weekday()]
        self.facility.workflow_config = {'operating_hours': self.daily_hours(), 'allowed_booking_days': [day]}
        self.facility.save(update_fields=['facility_type', 'slots', 'workflow_config'])
        closed = {**self.daily_hours(), day: None}
        for status in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED):
            booking = Booking.objects.create(id='KEEP-' + uuid.uuid4().hex[:10], facility=self.facility,
                booking_date=self.day, start_time='13:00', end_time='17:00', status=status)
            self.assertEqual(self.schedule_update(closed).status_code, 400)
            self.facility.refresh_from_db()
            self.assertEqual(self.facility.workflow_config['allowed_booking_days'], [day])
            self.assertEqual(self.facility.workflow_config['operating_hours'], self.daily_hours())
            booking.delete()
        self.assertEqual(self.schedule_update(closed).status_code, 200)
        self.facility.refresh_from_db()
        self.assertNotIn('allowed_booking_days', self.facility.workflow_config)
        path = f'/api/mobile/facilities/{self.facility.pk}/availability/'
        self.assertEqual(self.client.get(f'{path}?date={self.day}').json()['available_slots'], [])
        self.assertEqual(self.schedule_update(self.daily_hours()).status_code, 200)
        self.assertTrue(self.client.get(f'{path}?date={self.day}').json()['available_slots'])
        other_day = self.day + timedelta(days=1)
        self.assertTrue(self.client.get(f'{path}?date={other_day}').json()['available_slots'])
        self.facility.refresh_from_db()
        self.assertNotIn('allowed_booking_days', self.facility.workflow_config)

    def test_retired_day_fields_cannot_close_an_active_reservation(self):
        self.facility.facility_type = 'function_hall'
        self.facility.slots = ''
        self.facility.workflow_config = {'operating_hours': self.daily_hours()}
        self.facility.save(update_fields=['facility_type', 'slots', 'workflow_config'])
        booking = Booking.objects.create(id='KEEP-DAY-POLICY', facility=self.facility,
            booking_date=self.day, start_time='13:00', end_time='17:00', status='approved')
        result = self.schedule_update(self.daily_hours(), allowed_booking_days=[], weekend_only=True)
        self.assertEqual(result.status_code, 200, result.content)
        self.facility.refresh_from_db()
        self.assertNotIn('allowed_booking_days', self.facility.workflow_config)
        self.assertNotIn('weekend_only', self.facility.workflow_config)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'approved')
        result = self.client.get(f'/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}').json()
        self.assertTrue(result['available_slots'])
        self.assertIn('reserved', [row['status'] for row in result['slots']])

class MobileBookingConcurrencyTests(TransactionTestCase):
    """Separate real PostgreSQL transactions must not reserve the same interval."""
    # Existing unmanaged FKs need cascading cleanup in the disposable test DB.
    available_apps = ["accounts", "api", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions"]

    @classmethod
    def setUpClass(cls):
        tables = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Booking, FacilityPayment):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
        super().setUpClass()

    def test_simultaneous_mobile_submissions_create_only_one_reservation(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        MobileFacilityBookingTests.setUp(self)
        barrier = Barrier(2)
        data = self.data.copy()
        auth = self.auth.copy()

        def submit():
            connections.close_all()
            try:
                barrier.wait(timeout=15)
                response = Client().post("/api/mobile/bookings/", json.dumps({**data, "request_key": str(uuid.uuid4())}),
                    content_type="application/json", **auth)
                return response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: submit(), range(2)))
        self.assertEqual(sorted(results), [201, 400])
        self.assertEqual(Booking.objects.filter(facility=self.facility).count(), 1)
