import json
import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, FacilityPayment
from modules.messages.auth import mobile_chat_token


class MobileFacilityBookingTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Legacy tables are unmanaged; isolated test databases need their schema.
        tables = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Booking, FacilityPayment):
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
        self.assertEqual(self.post(f"/api/mobile/bookings/{booking_id}/cancel/", {}).status_code, 409)
        FacilityPayment.objects.create(id="PAY-TEST", booking_id=booking_id, payment_status="paid", paid_amount=2000, official_receipt_no="OR-TEST")
        response = self.client.get(f"/api/mobile/bookings/{booking_id}/", **self.auth).json()["booking"]
        self.assertTrue(response["can_view_slip"])
        self.assertEqual(response["payment_status"], "paid")
        self.assertEqual(response["receipts"][0]["number"], "OR-TEST")

    def test_session_rate_and_specialized_flow(self):
        self.facility.price_type = "session"
        self.facility.save()
        self.assertEqual(self.post(f"/api/mobile/facilities/{self.facility.pk}/quote/").json()["total_amount"], "500.00")
        self.facility.booking_mode = "service"
        self.facility.facility_type = "food_analysis"
        self.facility.save()
        self.assertEqual(self.post().status_code, 400)

    def test_admin_cannot_create_overlapping_schedule(self):
        self.post()
        admin = User.objects.create_user(username="booking-admin-" + uuid.uuid4().hex[:8], role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(admin)
        self.client.force_login(admin)
        response = self.client.post("/api/bookings/create/", json.dumps({"facility_id": self.facility.pk,
            "date": self.day.isoformat(), "start": "14:00", "end": "16:00", "type": "class"}), content_type="application/json")
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
            self.assertEqual(self.client.get(f"{path}/availability/?date={self.day}").json()["slots"][1]["status"], "reserved")
            self.assertEqual(self.post().status_code, 400)
            booking.delete()

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
