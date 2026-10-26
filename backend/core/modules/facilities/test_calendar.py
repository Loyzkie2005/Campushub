"""Calendar queries and UI fixtures use only isolated test-database records."""
import json
import base64
import os
import uuid
from datetime import datetime, time, timedelta
from pathlib import Path

from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from accounts.models import User, AccountActivity
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, FacilityPayment, Room, FacilityBookingRequest
from .services.calendar import calendar_data, calendar_events
from .services.mobile_booking import conflicting_bookings


class CalendarTests(TestCase):
    @classmethod
    def setUpClass(cls):
        tables = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.admin = User.objects.create_user(username='calendar-admin', role='Facilities Admin', is_staff=True)
        sync_user_admin_permissions(self.admin)
        self.client.force_login(self.admin)
        self.facility = Facility.objects.create(id='CALENDAR-COURT', facility_name='Calendar Court', facility_type='covered_court', booking_mode='slot')
        self.day = timezone.localdate()+timedelta(days=1)
        self.now = timezone.make_aware(datetime.combine(timezone.localdate(), time(12)))

    def booking(self, **changes):
        return Booking.objects.create(id='BK-'+uuid.uuid4().hex[:12], facility=self.facility, booking_date=self.day,
            start_time=time(13), end_time=time(15), purpose='[reservation] Test event\nReserved by: Actual Test Client', **changes)

    def block(self, kind='class', **config):
        row=self.booking(status='approved')
        row.purpose='['+kind+'] Actual block';row.save()
        FacilityBookingRequest.objects.create(booking=row, request_key=uuid.uuid4(), details={'source':'schedule','schedule':{
            'type':kind,'title':'Actual block','until':str(self.day),'repeat':'none','all_day':False,**config}})
        return row

    def get_calendar(self, **query):
        return self.client.get('/api/facility-calendar/', {'start':str(self.day),'end':str(self.day+timedelta(days=5)),**query})

    def test_status_payment_and_no_duplicate_or_service_records(self):
        pending=self.booking(status='pending');approved=self.booking(status='approved')
        self.booking(status='cancelled');self.booking(status='rejected');self.booking(status='completed')
        lab=Facility.objects.create(id='CALENDAR-LAB',facility_name='Actual Lab',facility_type='food_analysis',booking_mode='service')
        service=self.booking(status='approved');service.facility=lab;service.save()
        FacilityPayment.objects.create(booking=approved,payment_status='paid',paid_amount=0)
        before=Booking.objects.count(),FacilityBookingRequest.objects.count(),AccountActivity.objects.count()
        result=self.get_calendar().json()
        self.assertEqual({row['id'] for row in result['events']},{pending.pk,approved.pk})
        paid=next(row for row in result['events'] if row['id']==approved.pk)
        self.assertEqual(paid['status_label'],'Reserved / Confirmed')
        self.assertEqual(paid['payment_status'],'paid')
        self.assertEqual(before,(Booking.objects.count(),FacilityBookingRequest.objects.count(),AccountActivity.objects.count()))
        self.assertTrue(conflicting_bookings(self.facility,self.day,time(13),time(15)).filter(pk=pending.pk).exists())

    def test_filters_apply_to_month_and_upcoming(self):
        self.block('maintenance');self.block('official');self.block('hold');self.booking(status='approved')
        for kind in ('maintenance','official','hold','reservation'):
            result=self.get_calendar(type=kind,facility=self.facility.pk).json()
            self.assertEqual({row['type'] for row in result['events']},{kind})
            self.assertEqual({row['type'] for row in result['upcoming']},{kind})
        other=Facility.objects.create(id='CALENDAR-HALL',facility_name='Actual Hall',facility_type='function_hall',booking_mode='slot')
        row=self.booking(status='approved');row.facility=other;row.save()
        result=self.get_calendar(facility=other.pk).json()
        self.assertEqual({row['facility_id'] for row in result['events']},{other.pk})
        self.assertEqual({row['facility_id'] for row in result['upcoming']},{other.pk})

    def test_upcoming_is_independent_sorted_limited_and_excludes_ended(self):
        self.booking(status='approved')
        past=self.booking(status='approved');past.booking_date=timezone.localdate();past.start_time=time(8);past.end_time=time(10);past.save()
        for index in range(8):
            row=self.booking(status='approved');row.booking_date=self.day+timedelta(days=index+1);row.save()
        result=calendar_data(self.day-timedelta(days=100),self.day-timedelta(days=70),now=self.now)
        self.assertEqual(result['events'],[])
        self.assertEqual(len(result['upcoming']),5)
        self.assertEqual([row['date'] for row in result['upcoming']],sorted(row['date'] for row in result['upcoming']))
        self.assertNotIn(past.pk,{row['id'] for row in result['upcoming']})

    def test_recurrence_all_day_and_cancelled_or_inactive_blocks(self):
        row=self.block('class',until=str(self.day+timedelta(days=14)),repeat='weekly',weekdays=[self.day.weekday()],all_day=True)
        inactive=self.block('maintenance');inactive.status='rejected';inactive.save()
        cancelled=self.block('hold');cancelled.status='cancelled';cancelled.save()
        result=calendar_events(self.day,self.day+timedelta(days=14))
        self.assertEqual(len(result),3)
        self.assertEqual({item['id'] for item in result},{row.pk})
        self.assertTrue(all(item['all_day'] for item in result))
        self.assertEqual({item['first_date'] for item in result},{str(self.day)})
        self.assertNotIn(inactive.pk,{item['id'] for item in result})

    def test_room_stay_expansion_and_batched_queries(self):
        self.facility.booking_mode='room';self.facility.save()
        room=Room.objects.create(id=uuid.uuid4(),facility=self.facility,room_name='Actual Room 2')
        for index in range(10):
            row=self.booking(status='approved');row.booking_date=None;row.start_time=None;row.end_time=None
            row.check_in_date=self.day;row.check_out_date=self.day+timedelta(days=3);row.room_id=room.pk;row.save()
            FacilityBookingRequest.objects.create(booking=row,request_key=uuid.uuid4(),details={'check_in_time':'14:00','check_out_time':'12:00'})
        with self.assertNumQueries(3):
            events=calendar_events(self.day,self.day+timedelta(days=5))
        self.assertEqual(len(events),30)
        self.assertTrue(all(row['room']=='Actual Room 2' and row['start']=='14:00' for row in events))
        self.assertEqual(len(calendar_data(self.day,self.day+timedelta(days=5))['upcoming']),5)

    def test_completed_historical_only(self):
        row=self.booking(status='completed');row.booking_date=self.day-timedelta(days=3);row.save()
        result=calendar_data(self.day-timedelta(days=5),self.day+timedelta(days=5),now=self.now)
        self.assertEqual([item['id'] for item in result['events']],[row.pk])
        self.assertEqual(result['upcoming'],[])

    def test_validation_authentication_and_permission_separation(self):
        self.assertEqual(self.get_calendar(type='unsupported').status_code,400)
        self.assertEqual(self.get_calendar(end=str(self.day+timedelta(days=63))).status_code,400)
        self.assertEqual(self.get_calendar(start='invalid').status_code,400)
        self.client.logout();self.assertEqual(self.get_calendar().status_code,401)
        market=User.objects.create_user(username='calendar-market',role='Marketplace Admin',is_staff=True)
        sync_user_admin_permissions(market);self.client.force_login(market)
        self.assertEqual(self.get_calendar().status_code,403)
        self.assertEqual(self.client.get('/admin-calendar/').status_code,403)
        read=User.objects.create_user(username='calendar-view',is_staff=True)
        read.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(read)
        self.assertEqual(self.get_calendar().status_code,200)
        page=self.client.get('/admin-calendar/');self.assertEqual(page.status_code,200)
        self.assertNotContains(page,'id="bkUploadForm"')
        self.assertNotContains(page,'data-booking-kpi=')
        self.assertEqual(self.client.post('/api/bookings/create/',json.dumps({'type':'hold'}),content_type='application/json').status_code,403)

    def test_dynamic_facilities_and_honest_empty_state(self):
        Facility.objects.create(id='CAL-INACTIVE',facility_name='Inactive Test',availability_status='inactive')
        Facility.objects.create(id='CAL-ARCHIVED',facility_name='Archived Test',is_archived=True)
        Facility.objects.create(id='CAL-SERVICE',facility_name='Service Test',facility_type='food_analysis',booking_mode='service')
        page=self.client.get('/admin-calendar/')
        self.assertContains(page,'Calendar Court')
        for name in ('Inactive Test','Archived Test','Service Test'):
            self.assertNotContains(page,'>'+name+'</option>')
        self.assertEqual(self.get_calendar().json()['upcoming'],[])

    def test_readonly_attachment_is_private_and_does_not_grant_editing(self):
        block=self.block()
        details=block.mobile_request.details
        details['attachment']={'name':'reference.pdf','type':'application/pdf','data':base64.b64encode(b'%PDF-1.4 test').decode()}
        block.mobile_request.details=details;block.mobile_request.save()
        read=User.objects.create_user(username='calendar-evidence',is_staff=True)
        read.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(read)
        result=self.client.get(f'/api/facility-schedules/{block.pk}/attachment/')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result['Cache-Control'],'private, no-store')
        self.assertEqual(self.get_calendar()['Cache-Control'],'private, no-store')
        self.assertEqual(self.client.post(f'/api/facility-schedules/{block.pk}/update/',json.dumps({'action':'cancel'}),content_type='application/json').status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(f'/api/facility-schedules/{block.pk}/attachment/').status_code,401)

    def test_export_calendar_browser_fixtures(self):
        destination=os.environ.get('BOOKING_REVIEW_DIR')
        if not destination:return
        root=Path(destination);root.mkdir(parents=True,exist_ok=True)
        for kind in ('class','maintenance','official','hold','other'):
            self.block(kind,all_day=kind=='maintenance',until=str(self.day+timedelta(days=14)),repeat='weekly',weekdays=[self.day.weekday()])
        self.booking(status='pending');self.booking(status='approved')
        hostel=Facility.objects.create(id='CALENDAR-HOSTEL',facility_name='Calendar Hostel',facility_type='hostel',booking_mode='room')
        room=Room.objects.create(id=uuid.uuid4(),facility=hostel,room_name='Actual Room 2')
        stay=self.booking(status='approved');stay.facility=hostel;stay.booking_date=None;stay.start_time=None;stay.end_time=None
        stay.room_id=room.pk;stay.check_in_date=self.day;stay.check_out_date=self.day+timedelta(days=3);stay.save()
        FacilityBookingRequest.objects.create(booking=stay,request_key=uuid.uuid4(),details={'check_in_time':'14:00','check_out_time':'12:00'})
        root.joinpath('calendar-enhanced.html').write_bytes(self.client.get('/admin-calendar/').content)
        today=timezone.localdate();first=today.replace(day=1)
        last=(first.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1)
        for kind in ('all','maintenance','official','hold','reservation'):
            root.joinpath('calendar-'+kind+'.json').write_text(json.dumps(self.client.get('/api/facility-calendar/',
                {'start':str(first),'end':str(last),'type':kind}).json()),encoding='utf-8')
        root.joinpath('calendar-schedules.json').write_bytes(self.client.get('/api/facility-schedules/').content)
        read=User.objects.create_user(username='calendar-read-fixture',is_staff=True)
        read.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(read)
        root.joinpath('calendar-readonly.html').write_bytes(self.client.get('/admin-calendar/').content)
