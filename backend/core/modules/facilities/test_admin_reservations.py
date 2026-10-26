"""Admin/mobile parity and schedule history tests use only the isolated test database."""
import base64
import json
import os
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from accounts.models import AccountActivity, User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, FacilityBookingRequest, FacilityPayment, Room
from modules.messages.auth import mobile_chat_token
from .services.mobile_booking import conflicting_bookings


class AdminReservationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        tables = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.admin = User.objects.create_user(username="reservation-admin", role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(self.admin)
        self.client.force_login(self.admin)
        self.user = CampusHubUser.objects.create(username="reservation-client", first_name="Test", last_name="Client",
            student_id="TEST-123", email="client@example.edu", contact_number="09171234567", password_hash="unused")
        self.facility = Facility.objects.create(id="REAL-TEST-COURT", facility_name="Test Court", facility_type="covered_court",
            booking_mode="slot", slots="08:00-12:00;13:00-17:00", capacity=50, rate=Decimal("500"), price_type="hour")
        self.day = timezone.localdate() + timedelta(days=7)
        self.data = {"facility_id": self.facility.pk, "type": "reservation", "date": self.day.isoformat(),
            "start": "13:00", "end": "17:00", "purpose": "Test practice", "client_id": self.user.pk, "attendees": 20}
        self.block = {"facility_id": self.facility.pk, "type": "class", "date": self.day.isoformat(),
            "start": "13:00", "end": "15:00", "purpose": "Academic class"}

    def post(self, data, path="/api/bookings/create/"):
        return self.client.post(path, json.dumps(data), content_type="application/json")

    def test_client_search_is_bounded_and_permission_protected(self):
        response = self.client.get("/api/bookings/clients/?q=TEST-123")
        self.assertEqual(response.json()["clients"][0]["id"], self.user.pk)
        self.assertEqual(self.client.get("/api/bookings/clients/?q=Test%20Client").json()["clients"][0]["id"], self.user.pk)
        self.assertEqual(self.client.get("/api/bookings/clients/?q=T").json()["clients"], [])
        self.client.logout()
        self.assertEqual(self.client.get("/api/bookings/clients/?q=Test").status_code, 401)

    def test_manual_quote_and_core_record_reuse(self):
        result = self.post(self.data, "/api/bookings/preview/")
        self.assertEqual(result.json()["quote"]["total_amount"], "2000.00")
        response = self.post({**self.data, "total_amount": "1", "status": "approved"})
        self.assertEqual(response.status_code, 201, response.content)
        booking = Booking.objects.get(pk=response.json()["event"]["id"])
        self.assertEqual((booking.user_id, booking.status, booking.total_amount), (self.user.pk, "approved", Decimal("2000")))
        self.assertEqual(booking.mobile_request.details["source"], "admin")
        self.assertEqual(response.json()["event"]["source"], "Admin / Walk-in")
        self.assertTrue(AccountActivity.objects.filter(activity_type="reservation_created").exists())

    def test_schedule_preview_without_client_does_not_quote_or_save(self):
        data = {key:self.data[key] for key in ("facility_id","date","start","end")}
        result = self.post({**data,"availability_only":True}, "/api/bookings/preview/")
        self.assertEqual(result.json(), {"available":True})
        self.assertFalse(Booking.objects.exists())
        self.assertFalse(AccountActivity.objects.filter(activity_type="reservation_created").exists())
        self.assertEqual(self.post({**data,"availability_only":True}).status_code,400)
        from .services.operating_schedule import WEEKDAYS
        hours={day:{'open':'08:00','close':'17:00'} for day in WEEKDAYS}
        hours['thursday']=hours['saturday']=None
        self.facility.workflow_config={'operating_hours':hours};self.facility.save()
        options=self.client.get(f'/api/bookings/facilities/{self.facility.pk}/options/').json()['facility']
        for weekday in ('thursday','saturday'):
            selected=timezone.localdate()+timedelta(days=7+(WEEKDAYS.index(weekday)-timezone.localdate().weekday())%7)
            expected=f'{self.facility.facility_name} is not available on {weekday.title()}s. Please select an allowed operating day.'
            self.assertEqual(options['closed_operating_day_messages'][weekday],expected)
            result=self.post({**data,'date':selected.isoformat(),'availability_only':True},'/api/bookings/preview/')
            self.assertEqual(result.status_code,400)
            self.assertEqual(result.json()['error'],expected)
            self.assertFalse(result.json()['available'])
            self.assertFalse(Booking.objects.exists())
        friday=timezone.localdate()+timedelta(days=7+(4-timezone.localdate().weekday())%7)
        self.assertEqual(self.post({**data,'date':friday.isoformat(),'availability_only':True},'/api/bookings/preview/').json(),{'available':True})
        self.facility.workflow_config={'operating_hours':'Needs schedule review'};self.facility.save()
        self.assertEqual(self.client.get(f'/api/bookings/facilities/{self.facility.pk}/options/').json()['facility']['closed_operating_day_messages'],{})
        self.facility.workflow_config={};self.facility.save()
        self.assertEqual(self.post(self.block).status_code,201)
        result = self.post({**data,"availability_only":True}, "/api/bookings/preview/")
        self.assertEqual(result.status_code,400)
        self.assertIn("Class / Academic Schedule",result.json()["error"])
        self.assertIn("1:00 PM",result.json()["error"])
        self.assertNotIn("SC-",result.json()["error"])

    def test_pricing_failure_keeps_schedule_availability_honest(self):
        self.facility.price_type="custom"
        self.facility.save()
        result=self.post(self.data,"/api/bookings/preview/")
        self.assertEqual(result.status_code,400)
        self.assertEqual(result.json()["available"],True)
        self.assertEqual(result.json()["stage"],"pricing")
        self.assertNotIn("quote",result.json())

    def test_client_type_address_and_notes_are_validated_and_saved(self):
        self.assertEqual(self.post({**self.data,"client_type":"existing","client_id":""}).status_code,400)
        self.assertEqual(self.post({**self.data,"client_type":"walkin"}).status_code,400)
        self.facility.workflow_config={"requires_client_address":True}
        self.facility.save()
        self.assertEqual(self.post(self.data).status_code,400)
        response=self.post({**self.data,"client_type":"existing","address":"Test address","notes":"Keep entrance clear"})
        self.assertEqual(response.status_code,201,response.content)
        details=Booking.objects.get(pk=response.json()["event"]["id"]).mobile_request.details
        self.assertEqual((details["address"],details["notes"]),("Test address","Keep entrance clear"))

    def test_saved_slip_is_prefilled_and_protected(self):
        response=self.post(self.data)
        pk=response.json()["event"]["id"]
        page=self.client.get(f"/admin-bookings/{pk}/slip/")
        self.assertEqual(page.status_code,200)
        self.assertContains(page,"Facilities and Spaces Rental Booking Slip")
        self.assertContains(page,"Test Client")
        self.assertContains(page,"Test practice")
        self.assertContains(page,"PHP 2,000.00")
        self.assertNotContains(page,"<input")
        FacilityPayment.objects.create(id="SLIP-FAILED",booking_id=pk,payment_status="failed",paid_amount=2000)
        self.assertEqual(self.client.get(f'/api/bookings/{pk}/').json()['booking']['amount_due'],'2000.00')
        FacilityPayment.objects.create(id="SLIP-PAID",booking_id=pk,payment_status="paid",paid_amount=2000)
        self.assertEqual(self.client.get(f'/api/bookings/{pk}/').json()['booking']['amount_due'],'0.00')
        self.facility.workflow_config={"booking_form_type":"general"}
        self.facility.save()
        self.assertContains(self.client.get(f"/admin-bookings/{pk}/slip/"),"Facilities and Spaces Rental Booking Slip")
        reader=User.objects.create_user(username="booking-manager-only",is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename="can_manage_bookings",content_type__app_label="accounts"))
        self.client.force_login(reader)
        self.assertEqual(self.client.get(f"/admin-bookings/{pk}/slip/").status_code,200)
        self.client.logout()
        self.assertEqual(self.client.get(f"/admin-bookings/{pk}/slip/").status_code,401)

    def test_category_assigns_new_slip_and_saved_history_survives_reclassification(self):
        from .booking_workflow_views import document_values
        self.facility.workflow_config={"booking_form_type":"accommodation"}
        self.facility.save()
        response=self.post(self.data)
        self.assertEqual(response.status_code,201,response.content)
        pk=response.json()['event']['id']
        booking=Booking.objects.get(pk=pk)
        expected="Facilities and Spaces Rental Booking Slip"
        self.assertEqual(booking.mobile_request.details['quote']['form_label'],expected)
        self.assertEqual(self.client.get(f'/api/bookings/{pk}/').json()['booking']['quote']['form_label'],expected)
        self.assertEqual(self.client.get(f'/api/bookings/facilities/{self.facility.pk}/options/').json()['facility']['booking_form_label'],expected)
        snapshot=dict(booking.mobile_request.details)
        self.facility.facility_type='hostel';self.facility.workflow_config={'booking_form_type':'general'};self.facility.save()
        self.assertContains(self.client.get(f'/admin-bookings/{pk}/slip/'),expected)
        booking.refresh_from_db()
        self.assertEqual(document_values(booking,'slip')[0],expected)
        pdf=self.client.get(f'/api/bookings/{pk}/documents/slip/?format=pdf')
        self.assertEqual(pdf.status_code,200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertEqual(booking.mobile_request.details,snapshot)

    def test_walkin_reuses_nullable_user_and_does_not_create_account(self):
        before = CampusHubUser.objects.count()
        response = self.post({**self.data, "client_id": "", "full_name": "Walk-in Client", "contact_number": "09171234567"})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertIsNone(Booking.objects.get(pk=response.json()["event"]["id"]).user_id)
        self.assertEqual(CampusHubUser.objects.count(), before)

    def test_backend_rechecks_conflict_after_preview(self):
        self.assertEqual(self.post(self.data, "/api/bookings/preview/").status_code, 200)
        self.assertEqual(self.post(self.block).status_code, 201)
        self.assertEqual(self.post(self.data).status_code, 400)
        self.assertEqual(Booking.objects.count(), 1)

    def test_approval_configuration_and_stale_price(self):
        self.facility.workflow_config = {"requires_approval": False}
        self.facility.save()
        self.assertEqual(self.post({**self.data, "quoted_amount": "1.00"}).status_code, 400)
        response = self.post(self.data)
        self.assertEqual(response.json()["event"]["status"], "approved")

    def test_unavailable_status_capacity_hours_and_services(self):
        for changes in ({"attendees": 51}, {"attendees": -1}, {"date": "2000-01-01"}, {"start": "12:00"}):
            self.assertEqual(self.post({**self.data, **changes}).status_code, 400)
        self.facility.availability_status = "maintenance"
        self.facility.save()
        self.assertEqual(self.post(self.data).status_code, 400)
        self.facility.availability_status = "available"
        self.facility.facility_type = "food_analysis"
        self.facility.save()
        self.assertEqual(self.post(self.data).status_code, 400)
        self.assertEqual(self.post(self.block).status_code, 400)
        self.assertFalse(Booking.objects.exists())

    def test_weekly_block_controls_mobile_and_admin_without_duplicate_occurrences(self):
        until = self.day + timedelta(days=14)
        response = self.post({**self.block, "until": until.isoformat(), "repeat": "weekly", "weekdays": [self.day.weekday()]})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(response.json()["message"], "Facility schedule saved successfully.")
        record = Booking.objects.get()
        self.assertEqual(record.mobile_request.details["source"], "schedule")
        self.assertIsNone(record.user_id)
        self.assertEqual(record.total_amount, 0)
        self.assertFalse(FacilityPayment.objects.exists())
        self.assertNotIn("job_order", record.mobile_request.details)
        later = self.day + timedelta(days=7)
        self.assertTrue(conflicting_bookings(self.facility, later, timezone.datetime.strptime("13:00", "%H:%M").time(), timezone.datetime.strptime("17:00", "%H:%M").time()).exists())
        availability = self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={later}").json()
        self.assertEqual(availability["slots"][1]["status"], "class")
        self.assertEqual(self.post({**self.data, "date": later.isoformat()}).status_code, 400)
        calendar = self.client.get(f"/api/facility-calendar/?start={self.day}&end={until}").json()["events"]
        self.assertEqual(len(calendar), 3)
        self.assertEqual(len({row["id"] for row in calendar}), 1)
        page = self.client.get("/admin-bookings/")
        self.assertEqual(page.context["booking_requests"], [])

    def test_weekdays_not_selected_and_expired_blocks_do_not_conflict(self):
        response = self.post({**self.block, "until": (self.day + timedelta(days=7)).isoformat(), "repeat": "weekly", "weekdays": [(self.day.weekday()+1)%7]})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.post(self.data).status_code, 201)

    def test_schedule_edit_cancel_and_history(self):
        response = self.post(self.block)
        pk = response.json()["event"]["id"]
        path = f"/api/facility-schedules/{pk}/update/"
        self.assertEqual(self.post({**self.block, "start": "08:00", "end": "10:00"}, path).status_code, 200)
        count = AccountActivity.objects.count()
        self.assertEqual(self.post({**self.block, "start": "08:00", "end": "10:00"}, path).status_code, 200)
        self.assertEqual(AccountActivity.objects.count(), count)
        self.assertEqual(self.post({"action": "cancel"}, path).status_code, 200)
        self.assertTrue(Booking.objects.filter(pk=pk, status="cancelled").exists())
        self.assertEqual(self.post(self.data).status_code, 201)
        self.assertTrue(AccountActivity.objects.filter(activity_type="facility_block_cancelled").exists())

    def test_other_all_day_and_invalid_types(self):
        self.assertEqual(self.post({**self.block, "type": "assessment"}).status_code, 400)
        self.assertEqual(self.post({**self.block, "type": "other"}).status_code, 400)
        response = self.post({**self.block, "type": "other", "other_type": "Emergency work", "all_day": True, "start": "", "end": ""})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.post(self.data).status_code, 400)

    def test_attachment_download_is_private_and_does_not_create_availability_without_dates(self):
        attachment = {"name": "schedule.pdf", "type": "application/pdf", "data": base64.b64encode(b"%PDF-1.4\nreference").decode()}
        self.assertEqual(self.post({"facility_id": self.facility.pk, "type": "class", "attachment": attachment}).status_code, 400)
        response = self.post({**self.block, "attachment": attachment})
        self.assertEqual(response.status_code, 201, response.content)
        url = response.json()["event"]["attachment_url"]
        self.assertEqual(self.client.get(url).content, b"%PDF-1.4\nreference")
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 401)

    def test_rooms_use_exact_inventory_not_whole_facility_occupancy(self):
        self.facility.facility_type, self.facility.booking_mode, self.facility.price_type = "hostel", "room", "night"
        self.facility.save()
        first = Room.objects.create(id=uuid.uuid4(), facility=self.facility, room_name="Room A", capacity=2)
        second = Room.objects.create(id=uuid.uuid4(), facility=self.facility, room_name="Room B", capacity=2)
        stay = {**self.data, "check_in_date": self.day.isoformat(), "check_out_date": (self.day+timedelta(days=2)).isoformat(),
                "attendees": 2, "adults": 2, "children": 0, "room_id": str(first.pk)}
        response = self.post(stay)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["event"]["total_amount"], "1000.00")
        self.assertEqual(self.post(stay).status_code, 400)
        self.assertEqual(self.post({**stay, "room_id": str(second.pk)}).status_code, 201)
        self.assertEqual(self.post({**stay, "room_id": ""}).status_code, 400)

    def test_stay_preview_and_optional_adult_count(self):
        self.facility.facility_type,self.facility.booking_mode,self.facility.price_type="hostel","room","night"
        self.facility.save()
        room=Room.objects.create(id=uuid.uuid4(),facility=self.facility,room_name="Room A",capacity=3)
        schedule={"facility_id":self.facility.pk,"check_in_date":self.day.isoformat(),"check_out_date":(self.day+timedelta(days=2)).isoformat(),"room_id":str(room.pk)}
        self.assertEqual(self.post({**schedule,"availability_only":True},"/api/bookings/preview/").json(),{"available":True})
        response=self.post({**self.data,**schedule,"attendees":3,"adults":"","children":1})
        self.assertEqual(response.status_code,201,response.content)
        details=Booking.objects.get(pk=response.json()["event"]["id"]).mobile_request.details
        self.assertEqual((details["adults"],details["children"]),(2,1))
        history=self.client.get("/api/mobile/bookings/",HTTP_AUTHORIZATION="Bearer " + mobile_chat_token(self.user)).json()["bookings"]
        self.assertEqual((history[0]["date"],history[0]["check_in_date"],history[0]["check_out_date"]),(self.day.isoformat(),self.day.isoformat(),(self.day+timedelta(days=2)).isoformat()))
        self.assertEqual(response.json()["event"]["room"],"Room A")
        self.assertContains(self.client.get(f'/admin-bookings/{response.json()["event"]["id"]}/slip/'),"Room Accommodation Booking Slip")

    def test_saved_discount_fees_and_separate_deposit(self):
        self.facility.workflow_config = {"damage_deposit_applicable": True, "damage_deposit": {"type":"percentage","value":"10"},
            "additional_fees": [{"name":"Setup","amount":"100","unit":"booking","active":True}],
            "discount_rules": [{"eligible_client_type":"student","discount_type":"percentage","discount_value":"20","applies_to":"rental_fee","active":True}]}
        self.facility.save()
        self.assertEqual(self.post({**self.data, "discount_index": 0}, "/api/bookings/preview/").status_code, 400)
        result = self.post({**self.data, "discount_index": 0, "discount_reason": "Office checked student ID"}, "/api/bookings/preview/").json()["quote"]
        self.assertEqual((result["rental_amount"],result["fee_amount"],result["deposit_amount"],result["total_amount"]), ("1600.00","100.00","160.00","1860.00"))

    def test_shared_room_rate_requires_actual_same_room_occupancy(self):
        self.facility.booking_mode, self.facility.facility_type, self.facility.price_type = "room", "hostel", "person_night"
        self.facility.workflow_config = {"pricing":{"partner_rate":"300","partner_occupancy_required":2}}
        self.facility.save()
        room = Room.objects.create(id=uuid.uuid4(), facility=self.facility, room_name="Shared Room", capacity=3)
        stay = {**self.data,"check_in_date":self.day.isoformat(),"check_out_date":(self.day+timedelta(days=2)).isoformat(),
                "attendees":2,"adults":2,"children":0,"room_id":str(room.pk),"shared_rate":True}
        result = self.post(stay, "/api/bookings/preview/")
        self.assertEqual(result.json()["quote"]["total_amount"], "1200.00")
        self.assertEqual(self.post({**stay,"attendees":1,"adults":1}, "/api/bookings/preview/").status_code, 400)
        self.assertEqual(self.post({**stay,"room_id":""}, "/api/bookings/preview/").status_code, 400)

    def test_base_duration_item_fee_and_day_quotes_use_saved_configuration(self):
        self.facility.price_type = "base_hour"
        self.facility.workflow_config = {"pricing":{"base_duration":"2","additional_hour_rate":"100"},
            "additional_fees":[{"name":"Chairs","unit":"item","amount":"10","active":True}]}
        self.facility.save()
        quote = self.post({**self.data,"fee_quantities":{"0":3}}, "/api/bookings/preview/").json()["quote"]
        self.assertEqual(quote["total_amount"], "730.00")
        self.facility.price_type = "day"
        self.facility.workflow_config = {}
        self.facility.save()
        self.assertEqual(self.post(self.data, "/api/bookings/preview/").json()["quote"]["total_amount"], "500.00")

    def test_mobile_final_submission_obeys_new_recurring_block(self):
        self.post({**self.block,"until":(self.day+timedelta(days=7)).isoformat(),"repeat":"weekly","weekdays":[self.day.weekday()]})
        mobile = {**self.data,"date":(self.day+timedelta(days=7)).isoformat(),"request_key":str(uuid.uuid4()),
            "full_name":"Test Client","email":"client@example.edu","contact_number":"09171234567","event_name":"Test event"}
        response = self.client.post("/api/mobile/bookings/",json.dumps(mobile),content_type="application/json",
            HTTP_AUTHORIZATION="Bearer " + mobile_chat_token(self.user))
        self.assertEqual(response.status_code,400)
        self.assertEqual(Booking.objects.count(),1)

    def test_recurring_blocks_change_capacity_not_most_booked_ranking(self):
        from modules.marketplace.services.analytics import AnalyticsPeriod
        from modules.reports.dashboard_bookings import most_booked_facilities
        from modules.reports.dashboard_utilization import build_facility_utilization
        until = self.day + timedelta(days=7)
        self.post({**self.block,"until":until.isoformat(),"repeat":"weekly","weekdays":[self.day.weekday()]})
        self.post({**self.data,"start":"08:00","end":"12:00"})
        Booking.objects.filter(purpose__startswith="[reservation]").update(status="approved")
        period = AnalyticsPeriod("custom", "Custom Range", self.day, until)
        ranked = most_booked_facilities(period)
        self.assertEqual(ranked[0]["bookings"],1)
        row = next(item for item in build_facility_utilization(period)["rows"] if item["key"] == "covered_court")
        self.assertEqual(row["used"],4)
        self.assertEqual(row["capacity"],60)

    def test_schedule_permission_is_separate_and_csrf_is_required(self):
        limited = User.objects.create_user(username="reservation-only", is_staff=True)
        limited.user_permissions.add(Permission.objects.get(codename="can_book_facilities", content_type__app_label="accounts"))
        self.client.force_login(limited)
        self.assertEqual(self.post(self.data).status_code, 201)
        self.assertEqual(self.post(self.block).status_code, 403)
        from django.test import Client
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.admin)
        self.assertEqual(csrf.post("/api/bookings/create/", json.dumps(self.block), content_type="application/json").status_code, 403)

    def test_normal_booking_capability_does_not_allow_admin_client_search(self):
        normal = User.objects.create_user(username="ordinary-booker", role="User")
        normal.user_permissions.add(Permission.objects.get(codename="can_book_facilities", content_type__app_label="accounts"))
        self.client.force_login(normal)
        self.assertEqual(self.client.get("/api/bookings/clients/?q=Test").status_code,403)
        self.assertEqual(self.post(self.data).status_code,403)
        self.assertEqual(self.post(self.data,"/api/bookings/preview/").status_code,403)

    def test_export_browser_fixtures(self):
        destination = os.environ.get("BOOKING_REVIEW_DIR")
        if not destination:
            return
        root = Path(destination)
        root.mkdir(parents=True, exist_ok=True)
        root.joinpath("quote.json").write_text(json.dumps(self.post(self.data, "/api/bookings/preview/").json()), encoding="utf-8")
        root.joinpath("clients.json").write_text(json.dumps(self.client.get("/api/bookings/clients/?q=Test").json()), encoding="utf-8")
        root.joinpath("schedule-saved.json").write_bytes(self.post(self.block).content)
        self.post({**self.data, "start":"08:00", "end":"12:00"})
        root.joinpath("bookings.html").write_bytes(self.client.get("/admin-bookings/").content)
        root.joinpath("calendar.html").write_bytes(self.client.get("/admin-calendar/").content)
        root.joinpath("facility.json").write_text(json.dumps(self.client.get(f"/api/bookings/facilities/{self.facility.pk}/options/").json()), encoding="utf-8")
        root.joinpath("blocks.json").write_text(json.dumps(self.client.get("/api/facility-schedules/").json()), encoding="utf-8")
        root.joinpath("slots.json").write_text(json.dumps(self.client.get(f"/api/mobile/facilities/{self.facility.pk}/availability/?date={self.day}").json()), encoding="utf-8")
        root.joinpath("saved.json").write_text(json.dumps(self.post({**self.data,"date":(self.day+timedelta(days=1)).isoformat()}).json()),encoding="utf-8")
        saved=json.loads(root.joinpath("saved.json").read_text(encoding="utf-8"))
        root.joinpath("slip.html").write_bytes(self.client.get(f'/admin-bookings/{saved["event"]["id"]}/slip/').content)
        root.joinpath('reservation-detail.json').write_bytes(self.client.get(f'/api/bookings/{saved["event"]["id"]}/').content)
        root.joinpath('reservation-list.json').write_bytes(self.client.get('/api/bookings/').content)
        self.facility.facility_type,self.facility.booking_mode,self.facility.price_type="hostel","room","night"
        self.facility.workflow_config={"check_in_time":"14:00","check_out_time":"12:00","booking_form_type":"accommodation"}
        self.facility.save()
        root.joinpath("no-rooms.json").write_text(json.dumps(self.client.get(f"/api/bookings/facilities/{self.facility.pk}/options/").json()),encoding="utf-8")
        Room.objects.create(id=uuid.uuid4(),facility=self.facility,room_name="Test Room",capacity=3)
        root.joinpath("room-facility.json").write_text(json.dumps(self.client.get(f"/api/bookings/facilities/{self.facility.pk}/options/").json()),encoding="utf-8")
