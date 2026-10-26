"""Real transitions and permission boundaries, using isolated database records only."""
import base64
import json
import os
import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone
from decimal import Decimal
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
from lxml import etree as ET
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, Client
from django.utils import timezone

from accounts.models import User, AccountActivity
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, FacilityPayment, Room, FacilityBookingRequest
from modules.messages.auth import mobile_chat_token


class BookingWorkflowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        tables=connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser,Facility,Room,Booking,FacilityPayment):
                if model._meta.db_table not in tables: editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.admin=User.objects.create_user(username='workflow-admin',role='Facilities Admin',is_staff=True)
        sync_user_admin_permissions(self.admin);self.client.force_login(self.admin)
        self.user=CampusHubUser.objects.create(username='workflow-client',first_name='Real',last_name='Test',
            email='workflow@example.edu',contact_number='09171234567',password_hash='unused')
        self.facility=Facility.objects.create(id='WORKFLOW-COURT',facility_name='Workflow Court',facility_type='covered_court',
            booking_mode='slot',slots='08:00-12:00;13:00-17:00',rate=500,price_type='hour',capacity=50)
        self.day=timezone.localdate()+timedelta(days=7)
        self.data={'facility_id':self.facility.pk,'type':'reservation','date':str(self.day),'start':'13:00','end':'17:00',
            'purpose':'Training event','attendees':10,'client_type':'existing','client_id':self.user.pk}

    def post(self,path,data): return self.client.post(path,json.dumps(data),content_type='application/json')
    def create(self):
        response=self.post('/api/bookings/create/',self.data)
        self.assertEqual(response.status_code,201,response.content)
        return Booking.objects.get(pk=response.json()['event']['id'])
    def update(self,b,action,**data): return self.post(f'/api/bookings/{b.pk}/update/',{'action':action,**data})
    def capture_overview(self, name, booking):
        """Optional browser fixtures from these isolated database tests only."""
        destination=os.environ.get('BOOKING_OVERVIEW_REVIEW_DIR')
        if destination:
            root=Path(destination);root.mkdir(parents=True,exist_ok=True)
            root.joinpath(name+'.json').write_bytes(self.client.get(f'/api/bookings/{booking.pk}/').content)
            root.joinpath(name+'.html').write_bytes(self.client.get(f'/admin-bookings/{booking.pk}/').content)
    def capture_inspection_flow(self, name, booking):
        self.capture_overview(name,booking)
        destination=os.environ.get('BOOKING_OVERVIEW_REVIEW_DIR')
        if destination:
            root=Path(destination)
            root.joinpath(name+'-list.json').write_bytes(self.client.get('/api/bookings/').content)
            root.joinpath(name+'-list.html').write_bytes(self.client.get('/admin-bookings/').content)
    def job_document_xml(self, booking):
        response=self.client.get(f'/api/bookings/{booking.pk}/documents/job-order/?format=docx')
        self.assertEqual(response.status_code,200,response.content[:100])
        return ET.fromstring(ZipFile(BytesIO(response.content)).read('word/document.xml'))

    def job_document_text(self, booking):
        from .services.job_order_docx import NS
        return ''.join(self.job_document_xml(booking).xpath('//w:t/text()',namespaces=NS))

    def payment(self,b,**changes):
        return self.update(b,'payment',payment_method='Cash',amount_paid='2000.00',official_receipt_no='OR-WORKFLOW',
            paid_at=timezone.now().isoformat(),**changes)

    def test_manual_auto_approval_tracks_actual_admin(self):
        b=self.create();d=b.mobile_request.details
        self.assertEqual(b.status,'approved');self.assertEqual(d['approval']['by']['id'],self.admin.pk)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['booking']['payment_status'],'unpaid')
        self.assertNotIn('approve',detail['booking']['actions'])
        self.assertTrue(AccountActivity.objects.filter(activity_type='booking_auto_approved').exists())

    def test_no_approval_permission_stays_pending_even_if_facility_policy_false(self):
        admin=User.objects.create_user(username='booking-only',is_staff=True)
        admin.user_permissions.add(Permission.objects.get(codename='can_book_facilities',content_type__app_label='accounts'))
        self.facility.workflow_config={'requires_approval':False};self.facility.save()
        self.client.force_login(admin);b=self.create()
        self.assertEqual(b.status,'pending');self.assertNotIn('approval',b.mobile_request.details)
        self.assertEqual(self.update(b,'approve').status_code,403)

    def test_payment_requires_or_full_amount_and_approved_state(self):
        b=self.create()
        for change in ({'official_receipt_no':''},{'amount_paid':'500'},{'amount_paid':'NaN'},
                       {'paid_at':str(self.day)},{'payment_method':'Online'}):
            data={'action':'payment','payment_method':'Cash','amount_paid':'2000','official_receipt_no':'OR-1','paid_at':timezone.now().isoformat(),**change}
            self.assertEqual(self.post(f'/api/bookings/{b.pk}/update/',data).status_code,400)
        self.assertFalse(FacilityPayment.objects.exists())
        b.status='pending';b.save()
        self.assertEqual(self.payment(b).status_code,400)

    def test_paid_state_derived_and_retry_cannot_duplicate_payment(self):
        b=self.create();response=self.update(b,'payment',payment_method='Cash',amount_paid='2000.00',official_receipt_no='OR-WORKFLOW',paid_at=timezone.now().replace(second=0,microsecond=0).isoformat())
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['booking']['status_label'],'Reserved / Confirmed')
        self.assertEqual(response.json()['booking']['status'],'approved')
        self.assertEqual(response.json()['booking']['payment_status'],'paid')
        self.assertEqual(self.payment(b).status_code,400)
        self.assertEqual(FacilityPayment.objects.count(),1)
        self.assertTrue(AccountActivity.objects.filter(activity_type='booking_reserved').exists())

    def test_same_or_cannot_be_recorded_for_another_booking(self):
        b=self.create();self.payment(b)
        self.data['date']=str(self.day+timedelta(days=1));second=self.create()
        self.assertEqual(self.payment(second).status_code,400)

    def test_actions_enforce_permission_and_csrf(self):
        b=self.create();reader=User.objects.create_user(username='reader',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['booking']['actions'],[])
        self.assertEqual(self.payment(b).status_code,403)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin)
        self.assertEqual(csrf.post(f'/api/bookings/{b.pk}/update/',json.dumps({'action':'cancel','reason':'Test'}),content_type='application/json').status_code,403)
        self.client.logout();self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').status_code,401)

    def test_mobile_remains_pending_and_internal_metadata_is_private(self):
        data={**self.data,'full_name':'Real Test','event_name':'Class event','contact_number':'09171234567',
              'email':self.user.email,'request_key':str(uuid.uuid4())}
        auth={'HTTP_AUTHORIZATION':'Bearer '+mobile_chat_token(self.user)}
        result=self.client.post('/api/mobile/bookings/',json.dumps(data),content_type='application/json',**auth)
        self.assertEqual(result.status_code,201,result.content);b=Booking.objects.get(pk=result.json()['booking']['id'])
        self.assertEqual(b.status,'pending')
        self.assertEqual(self.client.get(f'/api/mobile/bookings/{b.pk}/slip/',**auth).status_code,409)
        approval=self.update(b,'approve');self.assertEqual(approval.status_code,200,approval.content)
        d=b.mobile_request.details;d.update(job_order={'internal':'Private'},inspections={'pre':{'remarks':'Private'}},verification_notes='Internal proof')
        FacilityBookingRequest.objects.filter(booking=b).update(details=d)
        detail=self.client.get(f'/api/mobile/bookings/{b.pk}/',**auth).json()['booking']
        self.assertEqual(detail['details']['quote']['rate'],'500.00')
        self.assertNotIn('job_order',detail['details']);self.assertNotIn('verification_notes',detail['details'])
        pdf=self.client.get(f'/api/mobile/bookings/{b.pk}/slip/',**auth)
        self.assertEqual(pdf.status_code,200);self.assertTrue(pdf.content.startswith(b'%PDF-'))
        other=CampusHubUser.objects.create(username='other-client',email='other@example.edu',password_hash='unused')
        self.assertEqual(self.client.get(f'/api/mobile/bookings/{b.pk}/slip/',HTTP_AUTHORIZATION='Bearer '+mobile_chat_token(other)).status_code,404)

    def test_mobile_job_order_service_matches_generated_draft_and_ignores_client_override(self):
        from api.views import serialize_facility
        from .services.job_order import default_job_order_service
        for kind, mode, expected in (
                ('covered_court', 'slot', 'Facility Rental'),
                ('function_hall', 'slot', 'Facility Rental'),
                ('hostel', 'room', 'Hotel Accommodation'),
                ('other', 'slot', ''), ('food_analysis', 'service', ''),
                ('training_kitchen', 'assessment', ''), ('lease_space', 'lease', ''),
                ('covered_court', 'service', '')):
            resource = Facility(facility_type=kind, booking_mode=mode)
            self.assertEqual(default_job_order_service(resource), expected)
            self.assertEqual(serialize_facility(resource)['job_order_service'], expected)
        self.assertEqual(default_job_order_service(None), '')
        data = {**self.data, 'full_name': 'Real Test', 'event_name': 'Class event',
            'contact_number': '09171234567', 'email': self.user.email,
            'request_key': str(uuid.uuid4()), 'additional_requirements': ['Sound System'],
            'job_order_service': 'Laboratory Analysis', 'job_order': {'approved': True}}
        auth = {'HTTP_AUTHORIZATION': 'Bearer ' + mobile_chat_token(self.user)}
        response = self.client.post('/api/mobile/bookings/', json.dumps(data),
            content_type='application/json', **auth)
        self.assertEqual(response.status_code, 201, response.content)
        row = response.json()['booking']
        self.assertEqual(row['facility']['job_order_service'], 'Facility Rental')
        booking = Booking.objects.get(pk=row['id'])
        self.assertEqual(booking.status, 'pending')
        self.assertNotIn('job_order', booking.mobile_request.details)
        approved = self.update(booking, 'approve')
        self.assertEqual(approved.status_code, 200, approved.content)
        details = FacilityBookingRequest.objects.get(booking=booking).details
        self.assertEqual(details['job_order']['service_types'], ['Facility Rental'])
        self.assertEqual(details['job_order']['document_status'], 'draft')
        self.assertIn('Class event', details['job_order']['specifics'])
        self.assertIn('Sound System', details['job_order']['items'])

    def test_approval_rechecks_other_conflicts_and_operating_schedule(self):
        b=self.create();b.status='pending';b.save()
        conflict=Booking.objects.create(id='WORKFLOW-CONFLICT',facility=self.facility,booking_date=self.day,start_time='14:00',end_time='16:00',status='approved')
        self.assertEqual(self.update(b,'approve').status_code,400)
        conflict.status='cancelled';conflict.save()
        self.facility.availability_status='maintenance';self.facility.save()
        self.assertEqual(self.update(b,'approve').status_code,400)

    def test_edit_excludes_only_itself_and_preserves_identity(self):
        b=self.create();preview=self.post('/api/bookings/preview/',{**self.data,'booking_id':b.pk})
        self.assertEqual(preview.status_code,200,preview.content)
        response=self.update(b,'edit',**{**self.data,'purpose':'Revised slip purpose'},quoted_amount='2000.00',notes='Updated')
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(Booking.objects.count(),1);b.refresh_from_db();self.assertEqual(b.mobile_request.details['notes'],'Updated')
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertIn('Revised slip purpose',detail['booking_form_html'])
        self.assertIn('edit',detail['booking']['actions'])
        self.assertIn('job_order',detail['booking']['actions'])
        self.payment(b);self.assertEqual(self.update(b,'edit',**self.data,quoted_amount='2000.00').status_code,400)
        paid_detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertNotIn('edit',paid_detail['booking']['actions'])
        self.assertIn('job_order',paid_detail['booking']['actions'])

    def test_job_order_is_structured_and_updates_one_record(self):
        b=self.create()
        self.assertEqual(self.update(b,'job_order',service_requested='Court rental',specifics='Practice').status_code,200)
        number=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']['number']
        self.assertEqual(self.update(b,'job_order',service_requested='Court rental',specifics='Revised').status_code,200)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']['number'],number)
        for suffix in ('','?format=pdf','?format=docx'):
            response=self.client.get(f'/api/bookings/{b.pk}/documents/job-order/{suffix}')
            self.assertEqual(response.status_code,200)
            if not suffix:
                self.assertContains(response,'data-job-preview')
                self.assertIn('Court rental',self.job_document_text(b))
                self.assertNotContains(response,'Reservation Date / Stay')
        self.assertEqual(Booking.objects.count(),1)
        page=self.client.get(f'/admin-bookings/{b.pk}/')
        self.assertEqual(page.status_code,200)
        self.assertContains(page,'bkTabJobOrder')
        self.assertContains(page,'bkPanelJobOrder')
        self.assertNotContains(page,'bkTabDocuments')
        self.assertNotContains(page,'bkBookingDetailsModal')

    def test_official_job_order_checkboxes_dates_and_saved_client(self):
        b=self.create()
        required='2026-12-20T13:00'
        response=self.update(b,'job_order',service_types=['Facility Rental','Equipment Rental','Facility Rental'],
            service_other='',specifics='Official <script>alert(1)</script>',items='Projector\nTables',
            gender_preference='Prefer not to say',required_at=required)
        self.assertEqual(response.status_code,200,response.content)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        job=detail['details']['job_order']
        self.assertEqual(job['service_types'],['Equipment Rental','Facility Rental'])
        self.assertEqual(job['service_requested'],'Equipment Rental; Facility Rental')
        self.assertEqual(job['required_at'],'2026-12-20T13:00:00+08:00')
        self.assertEqual(detail['job_order_form']['client']['name'],'Real Test')
        paper=self.client.get(f'/api/bookings/{b.pk}/documents/job-order/?format=docx')
        contents=self.job_document_text(b)
        for label in ('Name of Client','Gender Preference','Phone No.','Email Address','Details / Specifics',
                      'BPP NCII Assessment','Personnel In-charge','BEU Manager','Real Test'):
            self.assertIn(label,contents)
        self.assertIn('Official <script>alert(1)</script>',contents)
        self.assertIn('Dec 20, 2026 - 01:00 PM',contents)
        self.assertNotIn('workflow-admin',contents)
        from .services.job_order_docx import NS
        xml=self.job_document_xml(b)
        for identifier in (25,27,23):
            self.assertEqual(len(xml.xpath('//mc:AlternateContent[.//wp:docPr[@id=$id]]//a:custGeom/a:pathLst/a:path',namespaces=NS,id=str(identifier))),2)
        self.assertEqual(paper['Cache-Control'],'private, no-store')
        # Recorded staff are retained as workflow metadata, not forged paper signatures.
        self.assertEqual(job['assisted_by']['id'],self.admin.pk)
        self.assertEqual(job['filled_out_by']['id'],self.admin.pk)

    def test_job_order_rejects_invalid_choices_without_partial_write(self):
        b=self.create()
        original=dict(b.mobile_request.details['job_order'])
        for data in ({'service_types':[]}, {'service_types':'Facility Rental'},
                     {'service_types':['Invalid']}, {'service_types':[{}]},
                     {'service_types':['Facility Rental'],'gender_preference':'Invalid'},
                     {'service_types':['Facility Rental'],'required_at':'not-a-date'}):
            with self.subTest(data=data):
                response=self.update(b,'job_order',**data)
                self.assertEqual(response.status_code,400,response.content)
                b.refresh_from_db()
                self.assertEqual(b.mobile_request.details['job_order'],original)
        self.assertFalse(AccountActivity.objects.filter(activity_type='job_order_created').exists())

    def test_job_order_fills_original_package_and_private_downloads(self):
        from .services.job_order_docx import TEMPLATE, NS
        b=self.create()
        self.assertEqual(self.update(b,'job_order',number='BEU-OFFICE-001',service_types=[],
            service_other='Recorded service',specifics='Saved & <escaped> text',items='Chair').status_code,200)
        path=f'/api/bookings/{b.pk}/documents/job-order/'
        response=self.client.get(path+'?format=docx')
        self.assertEqual(response.status_code,200)
        with ZipFile(TEMPLATE) as source, ZipFile(BytesIO(response.content)) as filled:
            self.assertEqual(source.namelist(),filled.namelist())
            for name in source.namelist():
                if name!='word/document.xml':
                    self.assertEqual(source.read(name),filled.read(name),name)
        xml=self.job_document_xml(b)
        self.assertIn('BEU-OFFICE-001',self.job_document_text(b))
        self.assertFalse(xml.xpath('//w:rPr[count(w:b)>1]',namespaces=NS))
        self.assertIn('Saved & <escaped> text',self.job_document_text(b))
        signatures=xml.findall('w:body/w:tbl',NS)[1].findall('w:tr',NS)[1]
        self.assertFalse(''.join(signatures.xpath('.//w:t/text()',namespaces=NS)).strip())
        self.assertIn('attachment;',response['Content-Disposition'])
        self.assertIn('wordprocessingml.document',response['Content-Type'])
        inline=self.client.get(path+'?format=pdf&inline=1')
        attachment=self.client.get(path+'?format=pdf')
        self.assertEqual(inline.status_code,200)
        self.assertEqual(inline.content,attachment.content)
        self.assertIn('inline;',inline['Content-Disposition'])
        self.assertEqual(inline['X-Frame-Options'],'SAMEORIGIN')
        self.assertEqual(inline['X-Content-Type-Options'],'nosniff')
        self.client.logout()
        for suffix in ('?format=docx','?format=pdf&inline=1'):
            self.assertEqual(self.client.get(path+suffix).status_code,401)

    def test_job_order_legacy_write_in_and_number_survive_edit(self):
        b=self.create()
        self.assertEqual(self.update(b,'job_order',service_requested='Legacy court request').status_code,200)
        original=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']
        self.assertEqual(self.update(b,'job_order',service_types=[],service_other='Legacy court request',
            gender_preference='Female',specifics='Revised').status_code,200)
        revised=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']
        for key in ('number','date','filled_out_by'):
            self.assertEqual(revised[key],original[key])
        self.assertEqual(revised['service_other'],'Legacy court request')
        self.assertEqual(Booking.objects.count(),1)

    def test_official_job_order_pdf_is_a4_and_private(self):
        from io import BytesIO
        from pypdf import PdfReader
        b=self.create()
        self.assertEqual(self.update(b,'job_order',service_types=['Facility Rental'],
            gender_preference='Male',specifics='Saved details',items='Projector',
            received_at=timezone.now().replace(second=0,microsecond=0).isoformat(),required_at='2026-12-20T13:00').status_code,200)
        response=self.client.get(f'/api/bookings/{b.pk}/documents/job-order/?format=pdf')
        self.assertEqual(response.status_code,200,response.content[:100])
        pdf=PdfReader(BytesIO(response.content))
        self.assertEqual(len(pdf.pages),1)
        self.assertEqual((round(float(pdf.pages[0].mediabox.width)),round(float(pdf.pages[0].mediabox.height))),(595,842))
        content=' '.join(page.extract_text() for page in pdf.pages)
        for label in ('JOB ORDER', 'Real Test', 'Projector', 'BEU Manager', 'Saved details'):
            self.assertIn(label,content)
        for label in ('127.0.0.1','__at=','CampusHub |','workflow-admin'):
            self.assertNotIn(label,content)
        self.assertEqual(response['Cache-Control'],'private, no-store')
        destination=os.environ.get('JOB_ORDER_REVIEW_DIR')
        if destination:
            root=Path(destination);root.mkdir(parents=True,exist_ok=True)
            root.joinpath('job-order.pdf').write_bytes(response.content)
            root.joinpath('job-order.docx').write_bytes(self.client.get(f'/api/bookings/{b.pk}/documents/job-order/?format=docx').content)
            root.joinpath('job-order.html').write_bytes(self.client.get(f'/api/bookings/{b.pk}/documents/job-order/').content)
            root.joinpath('details-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
            root.joinpath('detail.json').write_bytes(self.client.get(f'/api/bookings/{b.pk}/').content)
            root.joinpath('options.json').write_bytes(self.client.get(f'/api/bookings/facilities/{self.facility.pk}/options/').content)
            self.assertEqual(self.update(b,'job_order',number='BEU-TEST-001',service_types=['Equipment Rental','Facility Rental'],
                gender_preference='Prefer not to say',specifics='Edited draft from test booking',items='Projector',
                required_at='2026-12-20T13:00').status_code,200)
            root.joinpath('edited-detail.json').write_bytes(self.client.get(f'/api/bookings/{b.pk}/').content)
            b.status='pending';b.save(update_fields=['status'])
            root.joinpath('pending-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
            b.status='approved';b.save(update_fields=['status'])
            reader=User.objects.create_user(username='job-order-reader',is_staff=True)
            reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
            self.client.force_login(reader)
            root.joinpath('readonly-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
            self.client.force_login(self.admin)
            self.data['date']=str(self.day+timedelta(days=1))
            auto=self.create()
            auto_pdf=self.client.get(f'/api/bookings/{auto.pk}/documents/job-order/?format=pdf')
            self.assertEqual(auto_pdf.status_code,200)
            self.assertEqual(len(PdfReader(BytesIO(auto_pdf.content)).pages),1)
            root.joinpath('auto-job-order.pdf').write_bytes(auto_pdf.content)
            root.joinpath('auto-page.html').write_bytes(self.client.get(f'/admin-bookings/{auto.pk}/').content)

    def test_job_order_long_content_flows_without_losing_text(self):
        from io import BytesIO
        from pypdf import PdfReader
        b=self.create()
        # Long real notes must continue rather than be cropped to the blank paper box.
        lines='\n'.join(f'Item {index}: recorded equipment' for index in range(45))
        self.assertEqual(self.update(b,'job_order',service_types=['Equipment Rental'],
            specifics='Long equipment request',items=lines).status_code,200)
        response=self.client.get(f'/api/bookings/{b.pk}/documents/job-order/?format=pdf')
        self.assertEqual(response.status_code,200)
        pdf=PdfReader(BytesIO(response.content));content=' '.join(page.extract_text() for page in pdf.pages)
        self.assertGreaterEqual(len(pdf.pages),2)
        self.assertIn('Item 0: recorded equipment',content)
        self.assertIn('Item 44: recorded equipment',content)
        self.assertIn('BEU Manager',content)
        destination=os.environ.get('JOB_ORDER_REVIEW_DIR')
        if destination:
            Path(destination).mkdir(parents=True,exist_ok=True)
            Path(destination,'job-order-long.pdf').write_bytes(response.content)

    def test_job_order_pdf_failure_preserves_record_and_word_access(self):
        from django.test import override_settings
        b=self.create()
        self.assertEqual(self.update(b,'job_order',service_types=['Facility Rental']).status_code,200)
        original=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']
        with override_settings(JOB_ORDER_OFFICE_BINARY='campushub-missing-office'):
            response=self.client.get(f'/api/bookings/{b.pk}/documents/job-order/?format=pdf')
        self.assertEqual(response.status_code,503)
        self.assertIn('Job Order',response.json()['error'])
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/job-order/').status_code,200)
        self.assertIn('Real Test',self.job_document_text(b))
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order'],original)
        self.client.logout()
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/job-order/').status_code,401)

    def test_approved_booking_prepares_draft_without_create_action(self):
        b=self.create();job=b.mobile_request.details['job_order']
        self.assertTrue(job['auto_generated'])
        self.assertEqual(job['document_status'],'draft')
        self.assertEqual(job['number'],'')
        self.assertEqual(job['service_types'],['Facility Rental'])
        for value in ('Facility: Workflow Court','Purpose: Training event','1:00 PM to 5:00 PM','Expected Participants: 10'):
            self.assertIn(value,job['specifics'])
        self.assertNotIn('approved_by',job)
        self.assertNotIn('received_at',job['specifics'])
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['job_order_status'],'Draft')
        self.assertTrue(detail['job_order_document'])
        self.assertNotIn('job_order_html',detail)
        self.assertNotIn('Not recorded',self.job_document_text(b))

    def test_booking_edit_refreshes_only_untouched_generated_draft(self):
        b=self.create();original=dict(b.mobile_request.details['job_order'])
        revised={**self.data,'date':str(self.day+timedelta(days=1)),'purpose':'Changed source purpose'}
        self.assertEqual(self.update(b,'edit',**revised,quoted_amount='2000.00').status_code,200)
        current=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']
        self.assertIn('Purpose: Changed source purpose',current['specifics'])
        self.assertIn((self.day+timedelta(days=1)).strftime('%b %d, %Y'),current['specifics'])
        self.assertEqual(current['prepared_at'],original['prepared_at'])
        self.assertEqual(self.update(b,'job_order',service_types=['Facility Rental'],specifics='Office-completed draft',number='OFFICE-01').status_code,200)
        revised['purpose']='Another booking edit'
        self.assertEqual(self.update(b,'edit',**revised,quoted_amount='2000.00').status_code,200)
        saved=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']
        self.assertEqual(saved['specifics'],'Office-completed draft')
        self.assertEqual(saved['number'],'OFFICE-01')

    def test_long_auto_filled_details_remain_editable_without_truncation(self):
        b=self.create();sidecar=b.mobile_request
        sidecar.details.update(purpose='Known purpose '*130,event_name='Known activity '*130)
        sidecar.details.pop('job_order');sidecar.save(update_fields=['details'])
        job=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']
        self.assertGreater(len(job['specifics']),2000)
        response=self.update(b,'job_order',number='OFFICE-LONG',service_types=['Facility Rental'],specifics=job['specifics'])
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']['specifics'],job['specifics'])

    def test_pending_booking_never_exposes_or_edits_job_order(self):
        self.facility.workflow_config={'job_order_stage':'request'};self.facility.save()
        b=Booking.objects.create(id='JO-PENDING',facility=self.facility,user=self.user,status='pending',
            booking_date=self.day,start_time='13:00',end_time='17:00',purpose='Pending request')
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertIsNone(detail['job_order_document'])
        self.assertNotIn('job_order',detail['booking']['actions'])
        self.assertFalse(any(doc['section']=='JobOrder' for doc in detail['documents']))
        self.assertEqual(self.update(b,'job_order',service_types=['Facility Rental']).status_code,400)
        for suffix in ('','?format=pdf','?format=docx'):
            self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/job-order/{suffix}').status_code,400)
        self.assertFalse(FacilityBookingRequest.objects.filter(booking=b).exists())
        self.assertEqual(self.update(b,'approve').status_code,200)
        b.refresh_from_db()
        self.assertEqual(b.mobile_request.details['job_order']['document_status'],'draft')

    def test_job_order_legacy_backfill_is_idempotent_and_preserves_sidecar(self):
        b=Booking.objects.create(id='JO-OLD',facility=self.facility,user=self.user,status='approved',
            booking_date=self.day,start_time='13:00',end_time='17:00',purpose='Legacy purpose')
        sidecar=FacilityBookingRequest.objects.create(booking=b,request_key=uuid.uuid4(),details={
            'full_name':'Saved Client','event_name':'Real activity','attendees':18,
            'additional_requirements':['Projector'],'quote':{'base_amount':'100'},'notes':'Keep history'})
        first=self.client.get(f'/api/bookings/{b.pk}/').json()
        prepared=first['details']['job_order']
        for value in ('Activity: Real activity','Purpose: Legacy purpose','Expected Participants: 18','Additional Requirements: Projector'):
            self.assertIn(value,prepared['specifics'])
        self.assertEqual(prepared['items'],'Projector')
        second=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(second['details']['job_order'],prepared)
        sidecar.refresh_from_db()
        self.assertEqual(sidecar.details['notes'],'Keep history')
        self.assertEqual(sidecar.details['quote'],{'base_amount':'100'})
        self.assertEqual(FacilityBookingRequest.objects.filter(booking=b).count(),1)
        self.assertEqual(Booking.objects.count(),1)
        self.assertEqual(self.update(b,'job_order',number='BEU-2026-001',service_types=['Facility Rental'],specifics='Office draft').status_code,200)
        edited=self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order']
        self.assertEqual(edited['number'],'BEU-2026-001')
        self.assertEqual(edited['specifics'],'Office draft')
        self.assertEqual(edited['prepared_at'],prepared['prepared_at'])

    def test_completed_legacy_job_order_backfills_and_stays_read_only(self):
        b=Booking.objects.create(id='JO-COMPLETED',facility=self.facility,user=self.user,status='completed',purpose='Past event')
        page=self.client.get(f'/admin-bookings/{b.pk}/')
        self.assertEqual(page.status_code,200)
        detail=page.context['booking_detail']
        self.assertTrue(detail['job_order_document'])
        self.assertEqual(detail['booking']['status'],'completed')
        self.assertNotIn('job_order',detail['booking']['actions'])
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/job-order/').status_code,200)
        self.assertEqual(FacilityBookingRequest.objects.filter(booking=b).count(),1)

    def test_job_order_category_mapping_uses_existing_type_and_stay(self):
        for category,expected in (('covered_court','Facility Rental'),('function_hall','Facility Rental'),('hostel','Hotel Accommodation')):
            with self.subTest(category=category):
                facility=Facility.objects.create(id='JO-'+category,facility_name='Configured '+category,facility_type=category,
                    booking_mode='room' if category=='hostel' else 'slot')
                b=Booking.objects.create(id='JO-MAP-'+category,facility=facility,status='approved',
                    check_in_date=self.day if category=='hostel' else None,
                    check_out_date=self.day+timedelta(days=2) if category=='hostel' else None)
                detail=self.client.get(f'/api/bookings/{b.pk}/').json()
                job=detail['details']['job_order']
                self.assertEqual(job['service_types'],[expected])
                from .services.job_order_docx import NS
                xml=self.job_document_xml(b)
                self.assertEqual(len(xml.xpath('//a:custGeom/a:pathLst[count(a:path)=2]',namespaces=NS)),1)
                self.assertNotIn('Not recorded',self.job_document_text(b))
                self.assertEqual(job['number'],'')
                self.assertEqual(job['turnaround_time'],'')
                if category=='hostel':self.assertIn('Stay:',job['specifics'])
                # Old optional JSON values can be NULL; the paper must keep blank lines.
                sidecar=FacilityBookingRequest.objects.get(booking=b)
                sidecar.details['job_order'].update(number=None,date=None,gender_preference=None,items=None,turnaround_time=None)
                sidecar.save(update_fields=['details'])
                html=self.client.get(f'/api/bookings/{b.pk}/documents/job-order/')
                self.assertEqual(html.status_code,200)
                self.assertNotContains(html,'None')

    def test_job_order_backfill_keeps_recorded_history_and_denies_unscoped_reads(self):
        b=self.create();sidecar=b.mobile_request
        existing={'number':'OLD-OFFICE-01','date':'2025-01-02','service_requested':'Historic service',
            'specifics':'Historical contents','approved_by':{'name':'Recorded actor'}}
        sidecar.details['job_order']=existing;sidecar.save(update_fields=['details'])
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['details']['job_order'],existing)
        legacy=Booking.objects.create(id='JO-PRIVATE-OLD',facility=self.facility,status='approved')
        self.client.logout()
        self.assertEqual(self.client.get(f'/api/bookings/{legacy.pk}/').status_code,401)
        self.assertFalse(FacilityBookingRequest.objects.filter(booking=legacy).exists())
        self.client.force_login(self.admin)
        for status in ('rejected','cancelled'):
            row=Booking.objects.create(id='JO-'+status,facility=self.facility,status=status)
            self.assertFalse(self.client.get(f'/api/bookings/{row.pk}/').json()['job_order_document'])
            self.assertFalse(FacilityBookingRequest.objects.filter(booking=row).exists())
        service=Facility.objects.create(id='JO-LAB',facility_name='Laboratory',facility_type='food_analysis',booking_mode='service')
        row=Booking.objects.create(id='JO-SERVICE',facility=service,status='approved')
        self.assertEqual(self.client.get(f'/api/bookings/{row.pk}/').status_code,404)
        self.assertFalse(FacilityBookingRequest.objects.filter(booking=row).exists())

    def test_required_inspections_block_early_completion(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True,'requires_post_use_inspection':True};self.facility.save()
        b=self.create();self.payment(b)
        self.assertEqual(self.update(b,'complete').status_code,400)
        self.assertEqual(self.update(b,'inspection',kind='post',has_damage=False,inspector_id=self.admin.pk,condition='Good Condition',inspected_at=timezone.now().isoformat()).status_code,400)
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        self.assertEqual(self.update(b,'complete').status_code,400)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        warning=next(c for c in detail['completion']['checks'] if c['key']=='pre_inspection')
        self.assertFalse(warning['blocking'])
        self.assertEqual(warning['message'],'Pre-use inspection was not recorded.')
        self.assertEqual(detail['completion']['remaining_count'],1)
        self.capture_overview('missed-pre',b)
        self.assertEqual(self.update(b,'inspection',kind='pre',inspector_id=self.admin.pk,condition='Good Condition',inspected_at=timezone.now().isoformat()).status_code,400)
        self.assertEqual(self.update(b,'inspection',kind='post',has_damage=False,inspector_id=self.admin.pk,condition='Good Condition',inspected_at=timezone.now().isoformat()).status_code,200)
        self.capture_overview('missed-pre-ready',b)
        self.assertEqual(self.update(b,'complete',issues_resolved_confirmed=True).status_code,200)

    def test_completion_readiness_matches_server_actions_and_rejects_bypass(self):
        b=self.create()
        self.assertEqual(self.payment(b).status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertFalse(detail['completion']['eligible'])
        self.assertNotIn('complete',detail['booking']['actions'])
        self.capture_overview('future-paid',b)
        response=self.update(b,'complete',issues_resolved_confirmed=True)
        self.assertEqual(response.status_code,400)
        self.assertIn('schedule has not ended',response.json()['error'])
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertTrue(detail['completion']['eligible'])
        self.assertIn('complete',detail['booking']['actions'])
        self.capture_overview('ready',b)
        self.assertFalse(detail['completion']['requires_issue_confirmation'])
        self.assertEqual(detail['completion']['remaining_count'],0)
        b.refresh_from_db()
        self.assertEqual(b.status,'approved')
        self.assertFalse(AccountActivity.objects.filter(activity_type='booking_completed').exists())

    def test_completion_records_actor_time_status_and_prevents_terminal_actions(self):
        b=self.create();self.payment(b)
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        self.capture_overview('ready-action',b)
        response=self.update(b,'complete',issues_resolved_confirmed=True)
        self.assertEqual(response.status_code,200,response.content)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['booking']['status'],'completed')
        self.assertEqual(detail['details']['completion']['by']['id'],self.admin.pk)
        self.assertTrue(detail['details']['completion']['at'])
        self.assertNotIn('issues_resolved_confirmed',detail['details']['completion'])
        self.capture_overview('completed',b)
        for action in ('complete','cancel'):
            self.assertNotIn(action,detail['booking']['actions'])
            self.assertEqual(self.update(b,action,reason='Attempted repeat',issues_resolved_confirmed=True).status_code,400)
        entry=AccountActivity.objects.get(activity_type='booking_completed')
        self.assertEqual(entry.metadata['booking_status'],'completed')
        self.assertEqual(entry.username,self.admin.username)
        self.assertEqual(entry.result,AccountActivity.RESULT_SUCCESS)

    def test_completion_requires_payment_and_saved_post_use_deposit_decision(self):
        self.facility.workflow_config={'requires_post_use_inspection':True,'damage_deposit_applicable':True,
            'damage_deposit':{'type':'fixed','value':'100'}}
        self.facility.save();b=self.create()
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        response=self.update(b,'complete',issues_resolved_confirmed=True)
        self.assertIn('Payment must be settled',response.json()['error'])
        self.capture_overview('unpaid',b)
        paid=self.update(b,'payment',payment_method='Cash',amount_paid='2100.00',official_receipt_no='OR-COMPLETE',
            paid_at=timezone.now().isoformat())
        self.assertEqual(paid.status_code,200,paid.content)
        response=self.update(b,'complete',issues_resolved_confirmed=True)
        self.assertIn('post-use inspection before',response.json()['error'])
        inspection={'kind':'post','has_damage':True,'inspector_id':self.admin.pk,'condition':'Minor Issues',
            'inspected_at':timezone.now().isoformat(),'damage_found':'Recorded finding needs office review'}
        self.assertEqual(self.update(b,'inspection',**inspection).status_code,200)
        response=self.update(b,'complete',issues_resolved_confirmed=True)
        self.assertIn('damage / deposit resolution',response.json()['error'])
        self.capture_overview('deposit-review',b)
        self.assertEqual(self.update(b,'inspection',**inspection,deposit_decision='Decision recorded by staff',issues_resolved_confirmed=True).status_code,200)
        self.assertTrue(self.client.get(f'/api/bookings/{b.pk}/').json()['completion']['eligible'])
        self.capture_overview('resolved-deposit',b)
        for confirmation in (None,False,'true'):
            response=self.update(b,'complete',issues_resolved_confirmed=confirmation)
            self.assertEqual(response.status_code,400)
            self.assertIn('Confirm that damage',response.json()['error'])
        self.assertEqual(self.update(b,'complete',issues_resolved_confirmed=True).status_code,200)
        self.assertEqual(FacilityPayment.objects.count(),1)
        self.capture_overview('resolved-deposit-completed',b)

    def test_pre_use_record_stays_completed_and_late_backfill_is_rejected(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save()
        b=self.create();self.payment(b)
        before=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertTrue(next(c for c in before['completion']['checks'] if c['key']=='pre_inspection')['blocking'])
        self.capture_overview('pre-before-use',b)
        self.assertEqual(self.update(b,'inspection',kind='pre',inspector_id=self.admin.pk,
            condition='Good Condition',inspected_at=timezone.now().isoformat()).status_code,200)
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        check=next(c for c in detail['completion']['checks'] if c['key']=='pre_inspection')
        self.assertTrue(check['satisfied'])
        self.assertTrue(detail['completion']['eligible'])
        self.assertNotIn('pre',detail['inspection_actions'])
        self.assertEqual(self.update(b,'inspection',kind='pre',inspector_id=self.admin.pk,
            condition='Good Condition',inspected_at=timezone.now().isoformat()).status_code,400)
        self.capture_overview('pre-recorded',b)

    def test_no_deposit_or_damage_does_not_invent_resolution_requirement(self):
        from .services.booking_workflow import completion_issues
        self.facility.workflow_config={'requires_post_use_inspection':True};self.facility.save()
        b=self.create();self.payment(b);b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        self.assertEqual(self.update(b,'inspection',kind='post',has_damage=False,inspector_id=self.admin.pk,
            condition='Good Condition',damage_found='No damage found.',missing_items='None',overtime='0',
            inspected_at=timezone.now().isoformat()).status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertTrue(detail['completion']['eligible'])
        self.assertFalse(detail['completion']['requires_issue_confirmation'])
        self.assertNotIn('resolution',[c['key'] for c in detail['completion']['checks']])
        self.assertFalse(completion_issues({'quote':{'deposit_amount':'unrecorded'}})['required'])
        for value in ('None','NoneType','null','0.00','N/A','Not recorded','No damage found.'):
            self.assertFalse(completion_issues({'quote':{'deposit_amount':'0'}}, {'damage_found':value})['required'])
        self.assertEqual(self.update(b,'complete').status_code,200)

    def test_real_damage_without_deposit_uses_existing_post_use_resolution(self):
        self.facility.workflow_config={'requires_post_use_inspection':True};self.facility.save()
        b=self.create();self.payment(b);b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        inspection={'kind':'post','has_damage':True,'inspector_id':self.admin.pk,'condition':'Damaged',
            'damage_found':'Broken chair','inspected_at':timezone.now().isoformat()}
        self.assertEqual(self.update(b,'inspection',**inspection).status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['completion']['remaining_count'],1)
        self.assertFalse(detail['completion']['eligible'])
        self.assertEqual(self.update(b,'complete',issues_resolved_confirmed=True).status_code,400)
        self.assertEqual(self.update(b,'inspection',**inspection,issues_resolved_confirmed=True).status_code,400)
        self.assertEqual(self.update(b,'inspection',**inspection,deposit_decision='Recorded repair settlement').status_code,200)
        self.assertFalse(self.client.get(f'/api/bookings/{b.pk}/').json()['completion']['eligible'])
        self.capture_overview('damage-review',b)
        self.assertEqual(self.update(b,'inspection',**inspection,deposit_decision='Recorded repair settlement',
            issues_resolved_confirmed=True).status_code,200)
        self.assertTrue(self.client.get(f'/api/bookings/{b.pk}/').json()['completion']['eligible'])
        self.assertEqual(self.update(b,'complete',issues_resolved_confirmed=True).status_code,200)

    def test_real_deposit_can_be_reviewed_without_creating_required_post_inspection(self):
        self.facility.workflow_config={'damage_deposit_applicable':True,'damage_deposit':{'type':'fixed','value':'100'}}
        self.facility.save();b=self.create()
        self.assertEqual(self.update(b,'payment',payment_method='Cash',amount_paid='2100',official_receipt_no='OR-DEPOSIT-REVIEW',
            paid_at=timezone.now().isoformat()).status_code,200)
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['completion']['remaining_count'],1)
        self.assertNotIn('post_inspection',[c['key'] for c in detail['completion']['checks']])
        self.assertIn('post',detail['inspection_actions'])
        self.capture_overview('deposit-only-review',b)
        self.assertEqual(self.update(b,'inspection',kind='post',has_damage=False,inspector_id=self.admin.pk,condition='Good Condition',
            inspected_at=timezone.now().isoformat(),deposit_decision='Staff-recorded deposit decision',issues_resolved_confirmed=True).status_code,200)
        self.assertTrue(self.client.get(f'/api/bookings/{b.pk}/').json()['completion']['eligible'])
        self.assertEqual(self.update(b,'complete',issues_resolved_confirmed=True).status_code,200)

    def test_completion_uses_manila_end_instant_and_fails_closed_without_checkout_time(self):
        from zoneinfo import ZoneInfo
        from .services.booking_workflow import completion_readiness
        b=self.create();self.payment(b)
        finish=timezone.make_aware(datetime.combine(b.booking_date,b.end_time),ZoneInfo('Asia/Manila'))
        with timezone.override('America/New_York'):
            with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=finish-timedelta(seconds=1)):
                self.assertFalse(completion_readiness(b)['eligible'])
            with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=finish):
                self.assertTrue(completion_readiness(b)['eligible'])
        b.check_out_date=timezone.localdate()-timedelta(days=1);b.end_time=None;b.save()
        self.assertFalse(completion_readiness(b)['eligible'])
        sidecar=b.mobile_request;sidecar.details={**sidecar.details,'check_out_time':'12:00'};sidecar.save()
        b.refresh_from_db()
        self.assertTrue(completion_readiness(b)['eligible'])

    def test_completion_readonly_and_inactive_statuses_cannot_complete(self):
        b=self.create();self.payment(b)
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        reader=User.objects.create_user(username='completion-reader',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertFalse(detail['completion']['can_manage'])
        self.capture_overview('readonly',b)
        self.assertNotIn('complete',detail['booking']['actions'])
        self.assertEqual(self.update(b,'complete',issues_resolved_confirmed=True).status_code,403)
        self.client.force_login(self.admin)
        for status in ('pending','rejected','cancelled','completed'):
            b.status=status;b.save()
            self.assertEqual(self.update(b,'complete',issues_resolved_confirmed=True).status_code,400)
            if status=='cancelled': self.capture_overview('cancelled',b)
        b.status='pending';b.save()
        sidecar=b.mobile_request;sidecar.details.pop('approval',None);sidecar.save()
        self.capture_overview('pending',b)
        self.assertEqual(self.update(b,'reject',reason='Recorded rejection reason').status_code,200)
        self.capture_overview('rejected',b)

    def test_pricing_method_uses_saved_method_then_existing_facility_configuration(self):
        from .services.booking_workflow import booking_row
        b=self.create()
        self.assertEqual(booking_row(b)['pricing_method_label'],'Per Hour')
        sidecar=b.mobile_request
        sidecar.details.pop('pricing_method',None)
        sidecar.details={**sidecar.details,'quote':{**sidecar.details['quote'],'price_type':'night'}};sidecar.save()
        b.refresh_from_db()
        self.assertEqual(booking_row(b)['pricing_method_label'],'Per Night')
        sidecar.details['pricing_method']='person_night';sidecar.save();b.refresh_from_db()
        self.assertEqual(booking_row(b)['pricing_method_label'],'Per Person / Per Night')
        sidecar.details['pricing_method']='unknown';sidecar.save();b.refresh_from_db()
        self.assertEqual(booking_row(b)['pricing_method_label'],'')
        self.capture_overview('unknown-pricing',b)

    def test_inspection_personnel_and_attachment_are_validated(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save();b=self.create()
        self.assertEqual(self.update(b,'inspection',kind='pre',inspector_id=999999,condition='Good Condition',inspected_at=timezone.now().isoformat()).status_code,400)
        fake={'type':'image/png','name':'fake.png','data':base64.b64encode(b'not an image').decode()}
        self.assertEqual(self.update(b,'inspection',kind='pre',inspector_id=self.admin.pk,condition='Good Condition',inspected_at=timezone.now().isoformat(),attachment=fake).status_code,400)

    def test_inspection_staff_choices_use_actual_active_user_and_group_grants_without_truncation(self):
        from django.contrib.auth.models import Group
        from accounts.models import Role
        from accounts.role_permissions import set_role_permissions
        from .services.inspections import authorized_inspectors
        permission=Permission.objects.get(codename='can_manage_bookings',content_type__app_label='accounts')
        User.objects.bulk_create([User(username=f'ordinary-{i}',role='User') for i in range(105)])
        role=Role.objects.create(role_name='Facilities Facilitator')
        set_role_permissions(role,['can_manage_bookings'])
        facilitator=User.objects.create_user(username='facilitator',role=role.role_name)
        sync_user_admin_permissions(facilitator)
        group=Group.objects.create(name='Authorized facility inspection staff');group.permissions.add(permission)
        grouped=User.objects.create_user(username='grouped',role='Personnel In-Charge');grouped.groups.add(group)
        blocked=[]
        for name,changes in [('student',{'role':'Student'}),('guest',{'role':'Guest/External'}),
            ('market',{'role':'Marketplace Admin','is_staff':True}),('inactive',{'is_active':False}),
            ('suspended',{'is_suspended':True})]:
            user=User.objects.create_user(username=name,**changes);user.user_permissions.add(permission);blocked.append(user)
        unrelated=User.objects.create_user(username='unrelated-admin',role='Other Office',is_staff=True)
        inactive_role=Role.objects.create(role_name='Inactive Personnel',is_active=False)
        disabled=User.objects.create_user(username='disabled-role',role=inactive_role.role_name)
        disabled.user_permissions.add(permission);blocked+=[unrelated,disabled]
        with self.assertNumQueries(1):
            ids=set(authorized_inspectors().values_list('pk',flat=True))
        self.assertTrue({self.admin.pk,facilitator.pk,grouped.pk}.issubset(ids))
        self.assertTrue(all(user.pk not in ids for user in blocked))
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save();b=self.create()
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual({s['id'] for s in detail['staff']},ids)
        self.assertIsNone(detail['inspection_defaults']['pre'])

    def test_inspection_actor_and_selected_inspector_are_authorized_independently(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save();b=self.create()
        permission=Permission.objects.get(codename='can_manage_bookings',content_type__app_label='accounts')
        student=User.objects.create_user(username='not-inspector',role='Student',is_staff=True)
        student.user_permissions.add(permission)
        data={'kind':'pre','inspector_id':student.pk,'condition':'Good Condition','inspected_at':timezone.now().isoformat()}
        self.assertEqual(self.update(b,'inspection',**data).status_code,400)
        self.client.force_login(student)
        data['inspector_id']=self.admin.pk
        self.assertEqual(self.update(b,'inspection',**data).status_code,403)
        self.assertNotIn('inspections',FacilityBookingRequest.objects.get(booking=b).details)

    def test_inspection_edit_preserves_evidence_history_and_records_actor_separately(self):
        from .services.schedules import metadata
        self.facility.workflow_config={'requires_pre_use_inspection':True,'requires_post_use_inspection':True}
        self.facility.save();b=self.create();self.payment(b)
        inspector=User.objects.create_user(username='actual-inspector',first_name='Actual',last_name='Inspector',role='Facilities Admin')
        sync_user_admin_permissions(inspector)
        file={'name':'inspection.pdf','type':'application/pdf','data':base64.b64encode(b'%PDF-1.4\ninspection evidence').decode()}
        data={'kind':'pre','inspector_id':inspector.pk,'condition':'Good Condition','existing_damage':'Existing wall mark',
              'inspected_at':timezone.now().isoformat(),'remarks':'Recorded before facility use'}
        self.capture_overview('inspection-pre-empty',b)
        response=self.update(b,'inspection',**data,attachment=file)
        self.assertEqual(response.status_code,200,response.content)
        stored=FacilityBookingRequest.objects.get(booking=b).details['inspections']['pre']
        self.assertEqual(stored['recorded_by']['id'],self.admin.pk)
        self.assertEqual(stored['inspector']['id'],inspector.pk)
        self.assertTrue(stored['created_at'])
        self.capture_overview('inspection-pre-recorded',b)
        sidecar=FacilityBookingRequest.objects.get(booking=b)
        sidecar.details['inspections']['pre']['cleanliness']='Historical setup finding'
        sidecar.save(update_fields=['details'])
        data['condition']='Minor Issues'
        self.assertEqual(self.update(b,'inspection',**data).status_code,200)
        b.refresh_from_db();saved=metadata(b)['inspections']['pre']
        self.assertEqual(saved['attachment'],file)
        self.assertEqual(saved['cleanliness'],'Historical setup finding')
        self.assertEqual(saved['created_at'],stored['created_at'])
        self.assertGreaterEqual(saved['at'],stored['at'])
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['inspection_defaults']['pre'],inspector.pk)
        self.assertNotIn(file['data'],json.dumps(detail))
        attachment=next(d for d in detail['documents'] if d['title']=='inspection.pdf')
        self.assertEqual(self.client.get(attachment['url']).content,base64.b64decode(file['data']))
        events=AccountActivity.objects.filter(metadata__booking_id=b.pk,activity_type__startswith='pre_use_inspection').order_by('created_at')
        self.assertEqual(list(events.values_list('activity_type',flat=True)),['pre_use_inspection_completed','pre_use_inspection_updated'])
        event=events.last();assert event is not None
        self.assertEqual(event.metadata['inspector_id'],inspector.pk)
        self.assertEqual(event.username,self.admin.username)
        self.assertEqual(event.metadata['inspected_at'],saved['inspected_at'])
        self.assertEqual(event.metadata['inspection_type'],'pre')
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        self.capture_overview('inspection-post-empty',b)
        self.assertEqual(self.update(b,'inspection',kind='post',has_damage=False,inspector_id=self.admin.pk,
            condition='Good Condition',inspected_at=timezone.now().isoformat()).status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['details']['inspections']['post']['inspector']['id'],self.admin.pk)
        self.assertEqual(detail['details']['inspections']['pre']['inspector']['id'],inspector.pk)
        self.assertTrue(detail['completion']['eligible'])
        self.capture_overview('inspection-post-no-damage',b)
        inspector.is_active=False;inspector.save()
        self.assertIsNone(self.client.get(f'/api/bookings/{b.pk}/').json()['inspection_defaults']['pre'])

    def test_post_inspection_requires_explicit_boolean_and_conditional_damage_description(self):
        self.facility.workflow_config={'requires_post_use_inspection':True};self.facility.save()
        b=self.create();self.payment(b);b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        data={'kind':'post','inspector_id':self.admin.pk,'condition':'Good Condition','inspected_at':timezone.now().isoformat()}
        for answer in (None,'false',0,1,True):
            response=self.update(b,'inspection',**data,has_damage=answer)
            self.assertEqual(response.status_code,400,response.content)
        self.assertEqual(AccountActivity.objects.filter(activity_type='post_use_inspection_completed').count(),0)
        response=self.update(b,'inspection',**data,has_damage=True,damage_found='Broken chair')
        self.assertEqual(response.status_code,200,response.content)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertTrue(detail['inspection_damage'])
        self.assertTrue(detail['completion']['requires_issue_confirmation'])
        self.capture_overview('inspection-post-damage',b)
        self.assertEqual(self.update(b,'inspection',**data,has_damage=True,damage_found='Broken chair',
            deposit_decision='Repair settled',issues_resolved_confirmed=True).status_code,200)
        response=self.update(b,'inspection',**data,has_damage=False,damage_found='Stale hidden description')
        self.assertEqual(response.status_code,200,response.content)
        record=FacilityBookingRequest.objects.get(booking=b).details['inspections']['post']
        self.assertFalse(record['has_damage']);self.assertEqual(record['damage_found'],'')
        self.assertEqual(record['deposit_decision'],'Repair settled')
        self.assertTrue(self.client.get(f'/api/bookings/{b.pk}/').json()['completion']['eligible'])
        self.capture_overview('inspection-post-updated',b)

    def test_legacy_inspection_reports_keep_unknown_damage_and_historical_findings(self):
        from .booking_workflow_views import document_values
        from .services.inspections import damage_state
        b=self.create();sidecar=b.mobile_request
        legacy={'inspector':{'id':self.admin.pk,'name':'Recorded inspector'},'condition':'Good Condition',
            'cleanliness':'Historical finding','damage_found':'','at':timezone.now().isoformat()}
        sidecar.details['inspections']={'post':legacy};sidecar.save(update_fields=['details'])
        b.refresh_from_db();title,values=document_values(b,'post-inspection');values=dict(values)
        self.assertEqual(values['Damage Found'],'Not recorded')
        self.assertNotIn('Created At',values)
        self.assertIn('Cleanliness (previously recorded)',values)
        self.assertIsNone(damage_state(legacy))
        self.assertFalse(damage_state({'damage_found':'No damage found.'}))
        self.assertTrue(damage_state({'damage_found':'Broken chair'}))
        self.assertFalse(damage_state({'has_damage':False,'damage_found':'Old description'}))
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/post-inspection/?format=pdf').status_code,200)

    def test_inspection_reader_can_view_reports_but_cannot_edit_or_upload(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save();b=self.create()
        data={'kind':'pre','inspector_id':self.admin.pk,'condition':'Good Condition','inspected_at':timezone.now().isoformat()}
        self.assertEqual(self.update(b,'inspection',**data).status_code,200)
        reader=User.objects.create_user(username='inspection-reader',is_staff=True,role='Records Office')
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['staff'],[]);self.assertEqual(detail['inspection_actions'],[])
        self.assertEqual(detail['details']['inspections']['pre']['condition'],'Good Condition')
        self.capture_overview('inspection-readonly',b)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/pre-inspection/').status_code,200)
        self.assertEqual(self.update(b,'inspection',**data).status_code,403)

    def test_inspection_condition_choices_validate_other_and_preserve_legacy_text(self):
        from .services.inspections import CONDITION_CHOICES
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save();b=self.create()
        data={'kind':'pre','inspector_id':self.admin.pk,'condition':'Other','inspected_at':timezone.now().isoformat()}
        self.assertEqual(self.update(b,'inspection',**data).status_code,400)
        data['condition']='Unconfigured condition'
        self.assertEqual(self.update(b,'inspection',**data).status_code,400)
        data['condition']='Other'
        self.assertEqual(self.update(b,'inspection',**data,condition_other='Equipment secured for assessment').status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['inspection_condition_choices'],list(CONDITION_CHOICES))
        self.assertEqual(detail['inspection_conditions']['pre']['label'],'Other: Equipment secured for assessment')
        self.capture_inspection_flow('flow-other',b)
        data['condition']='Requires Maintenance'
        self.assertEqual(self.update(b,'inspection',**data,condition_other='Ignore stale hidden text').status_code,200)
        record=FacilityBookingRequest.objects.get(booking=b).details['inspections']['pre']
        self.assertEqual(record['condition_other'],'')
        sidecar=FacilityBookingRequest.objects.get(booking=b)
        sidecar.details['inspections']['pre']['condition']='Historical custom finding';sidecar.save()
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['inspection_conditions']['pre'],{'value':'Other','other':'Historical custom finding','label':'Historical custom finding'})
        self.capture_inspection_flow('flow-legacy-condition',b)

    def test_personnel_assignment_validates_accounts_defaults_new_inspections_and_keeps_actual_inspectors(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True,'requires_post_use_inspection':True}
        self.facility.save();b=self.create()
        other=User.objects.create_user(username='assigned-facilitator',first_name='Assigned',last_name='Facilitator',role='Facilities Admin')
        sync_user_admin_permissions(other)
        self.capture_inspection_flow('flow-unassigned',b)
        self.assertEqual(self.update(b,'assign_personnel',personnel_id=self.user.pk+100000).status_code,400)
        response=self.update(b,'assign_personnel',personnel_id=other.pk)
        self.assertEqual(response.status_code,200,response.content)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['inspection_defaults'],{'pre':other.pk,'post':other.pk})
        self.assertEqual(detail['details']['assigned_personnel']['by']['id'],self.admin.pk)
        self.capture_inspection_flow('flow-assigned',b)
        event=AccountActivity.objects.get(activity_type='booking_personnel_assigned')
        self.assertEqual(event.metadata['personnel_id'],other.pk)
        response=self.update(b,'assign_personnel',personnel_id=other.pk)
        self.assertFalse(response.json()['changed'])
        self.assertEqual(AccountActivity.objects.filter(activity_type='booking_personnel_assigned').count(),1)
        self.assertEqual(self.update(b,'inspection',kind='pre',condition='Good Condition',inspector_id=self.admin.pk,
            inspected_at=timezone.now().isoformat()).status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['inspection_defaults'],{'pre':self.admin.pk,'post':other.pk})
        other.is_active=False;other.save()
        self.assertIsNone(self.client.get(f'/api/bookings/{b.pk}/').json()['inspection_defaults']['post'])
        self.assertEqual(self.update(b,'assign_personnel',personnel_id=other.pk).status_code,400)
        self.assertEqual(self.update(b,'assign_personnel',personnel_id=self.admin.pk).status_code,200)
        b.status='completed';b.save()
        self.assertEqual(self.update(b,'assign_personnel',personnel_id=self.admin.pk).status_code,400)

    def test_unchanged_inspection_does_not_write_or_duplicate_audit(self):
        from .services.schedules import metadata
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save();b=self.create()
        data={'kind':'pre','inspector_id':self.admin.pk,'condition':'Good Condition','inspected_at':timezone.now().isoformat()}
        self.assertEqual(self.update(b,'inspection',**data).status_code,200)
        b.refresh_from_db();before=metadata(b);updated=b.updated_at
        count=AccountActivity.objects.filter(metadata__booking_id=b.pk).count()
        data['inspected_at']=datetime.fromisoformat(data['inspected_at']).astimezone(timezone.get_default_timezone()).isoformat()
        response=self.update(b,'inspection',**data)
        self.assertFalse(response.json()['changed'])
        b.refresh_from_db();self.assertEqual(metadata(b),before);self.assertEqual(b.updated_at,updated)
        self.assertEqual(AccountActivity.objects.filter(metadata__booking_id=b.pk).count(),count)
        data['remarks']='A real follow-up remark'
        self.assertTrue(self.update(b,'inspection',**data).json()['changed'])
        self.assertEqual(AccountActivity.objects.filter(activity_type='pre_use_inspection_updated').count(),1)

    def test_inspection_shortcuts_follow_phase_records_readonly_and_completion(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True,'requires_post_use_inspection':True}
        self.facility.save();b=self.create();self.payment(b)
        def shortcuts():return self.client.get(f'/api/bookings/{b.pk}/').json()['booking']['inspection_shortcuts']
        self.assertEqual([s['action'] for s in shortcuts()],['inspection_pre'])
        self.assertEqual(self.update(b,'inspection',kind='pre',condition='Good Condition',inspector_id=self.admin.pk,
            inspected_at=timezone.now().isoformat()).status_code,200)
        self.assertEqual([s['action'] for s in shortcuts()],['pre_inspection_details'])
        self.capture_inspection_flow('flow-before-use',b)
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        self.assertEqual([s['action'] for s in shortcuts()],['pre_inspection_details','inspection_post'])
        self.capture_inspection_flow('flow-after-use',b)
        data={'kind':'post','has_damage':False,'condition':'Good Condition','inspector_id':self.admin.pk,'inspected_at':timezone.now().isoformat()}
        self.assertEqual(self.update(b,'inspection',**data).status_code,200)
        self.assertEqual([s['action'] for s in shortcuts()],['inspection_details'])
        self.capture_inspection_flow('flow-both-recorded',b)
        reader=User.objects.create_user(username='flow-reader',role='Records Office',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        self.assertEqual([s['action'] for s in shortcuts()],['inspection_details'])
        self.assertEqual(self.update(b,'assign_personnel',personnel_id=self.admin.pk).status_code,403)
        self.assertEqual(self.update(b,'inspection',**data).status_code,403)
        self.capture_inspection_flow('flow-readonly',b)
        self.client.force_login(self.admin)
        self.assertEqual(self.update(b,'complete').status_code,200)
        self.capture_inspection_flow('flow-completed',b)
        self.assertEqual(self.update(b,'cancel',reason='Invalid late cancellation').status_code,400)
        self.assertEqual(self.update(b,'inspection',**data).status_code,400)

    def test_damage_and_resolution_activity_only_records_real_state_changes(self):
        self.facility.workflow_config={'requires_post_use_inspection':True};self.facility.save();b=self.create();self.payment(b)
        b.booking_date=timezone.localdate()-timedelta(days=1);b.save()
        data={'kind':'post','has_damage':True,'condition':'Damaged','damage_found':'Chair damage confirmed',
              'inspector_id':self.admin.pk,'inspected_at':timezone.now().isoformat()}
        self.assertEqual(self.update(b,'inspection',**data).status_code,200)
        self.assertEqual(AccountActivity.objects.filter(activity_type='booking_damage_recorded').count(),1)
        self.assertFalse(self.update(b,'inspection',**data).json()['changed'])
        data.update(deposit_decision='Repair decision recorded',issues_resolved_confirmed=True)
        self.assertTrue(self.update(b,'inspection',**data).json()['changed'])
        self.assertEqual(AccountActivity.objects.filter(activity_type='booking_resolution_completed').count(),1)
        self.assertFalse(self.update(b,'inspection',**data).json()['changed'])
        self.assertEqual(AccountActivity.objects.filter(activity_type='booking_resolution_completed').count(),1)
        self.assertTrue(self.client.get(f'/api/bookings/{b.pk}/').json()['completion']['eligible'])

    def test_documents_are_private_and_not_public_media(self):
        b=self.create();file={'name':'reference.pdf','type':'application/pdf','data':base64.b64encode(b'%PDF-1.4\nreference').decode()}
        self.assertEqual(self.update(b,'document',title='Client reference',attachment=file).status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertNotIn('"data":',json.dumps(detail))
        self.assertNotIn(file['data'],json.dumps(detail))
        url=detail['documents'][-1]['url'];self.assertEqual(self.client.get(url).content,b'%PDF-1.4\nreference')
        self.client.logout();self.assertEqual(self.client.get(url).status_code,401)

    def test_cancel_and_reject_require_reason_keep_payment_history(self):
        b=self.create();self.assertEqual(self.update(b,'cancel').status_code,400)
        self.payment(b);self.assertEqual(self.update(b,'cancel',reason='Client cancellation').status_code,200)
        self.assertEqual(FacilityPayment.objects.count(),1)
        self.assertEqual(self.update(b,'payment').status_code,400)

    def cancelled_history(self):
        """Isolated historical fixture with real existing document/payment helpers."""
        from .services.booking_workflow import save_details
        b=self.create()
        self.assertEqual(self.update(b,'job_order',service_types=['Facility Rental'],
            specifics='Retain historical office request',items='Projector').status_code,200)
        self.assertEqual(self.payment(b,attachment={'name':'receipt.pdf','type':'application/pdf',
            'data':base64.b64encode(b'%PDF-test-receipt').decode()}).status_code,200)
        b.refresh_from_db();details=dict(b.mobile_request.details)
        details['inspections']={'pre':{'condition':'Good Condition','inspector':{'id':self.admin.pk,'name':'Inspector'},
            'inspected_at':timezone.now().isoformat(),'remarks':'Historical inspection',
            'attachment':{'name':'evidence.pdf','type':'application/pdf',
                'data':base64.b64encode(b'%PDF-test-evidence').decode()}}}
        save_details(b,details)
        self.assertEqual(self.update(b,'cancel',reason='Client withdrew the reservation').status_code,200)
        b.refresh_from_db()
        return b

    def test_cancelled_history_rejects_all_workflow_writes_and_keeps_private_records(self):
        from .services.booking_workflow import ACTION_PERMISSIONS,CANCELLED_READ_ONLY
        b=self.cancelled_history()
        original=b.mobile_request.details.copy()
        payments=list(FacilityPayment.objects.filter(booking=b).values())
        events=AccountActivity.objects.count()
        for action in set(ACTION_PERMISSIONS)-{'archive','restore'}:
            with self.subTest(action=action):
                response=self.update(b,action)
                self.assertEqual(response.status_code,400,response.content)
                self.assertEqual(response.json()['error'],CANCELLED_READ_ONLY)
        b.refresh_from_db()
        self.assertEqual(b.status,'cancelled')
        self.assertEqual(b.mobile_request.details,original)
        self.assertEqual(list(FacilityPayment.objects.filter(booking=b).values()),payments)
        self.assertEqual(AccountActivity.objects.count(),events)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['booking']['actions'],['archive'])
        self.assertEqual(detail['inspection_actions'],[])
        self.assertEqual(detail['booking']['payment_status'],'paid')
        self.assertIn('Retain historical office request',self.job_document_text(b))
        self.assertIn('Training event',detail['booking_form_html'])
        self.assertEqual(detail['details']['cancel']['reason'],'Client withdrew the reservation')
        self.assertEqual(self.client.get(detail['payments'][0]['receipt_attachment']['url']).content,b'%PDF-test-receipt')
        inspection=next(doc for doc in detail['documents'] if doc['section']=='Inspection' and '/attachments/' in doc['url'])
        self.assertEqual(self.client.get(inspection['url']).content,b'%PDF-test-evidence')
        self.capture_inspection_flow('cancelled-history',b)
        self.client.logout()
        self.assertEqual(self.client.get(detail['payments'][0]['receipt_attachment']['url']).status_code,401)

    def test_cancelled_archive_restore_preserves_status_finances_and_history(self):
        b=self.cancelled_history();history=dict(b.mobile_request.details)
        payments=list(FacilityPayment.objects.filter(booking=b).values())
        self.assertEqual(self.update(b,'archive').status_code,200)
        b.refresh_from_db();self.assertEqual(b.status,'cancelled')
        self.assertTrue(b.mobile_request.details['archive']['is_archived'])
        for key,value in history.items(): self.assertEqual(b.mobile_request.details[key],value)
        self.assertEqual(self.client.get('/api/bookings/').json()['total'],0)
        archived=self.client.get('/api/bookings/?record_status=archived').json()
        self.assertEqual(archived['bookings'][0]['actions'],['restore'])
        self.assertEqual(self.client.get('/api/bookings/?record_status=all').json()['total'],1)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').status_code,200)
        self.capture_inspection_flow('archived-history',b)
        destination=os.environ.get('BOOKING_OVERVIEW_REVIEW_DIR')
        if destination:
            Path(destination,'archived-history-list.json').write_bytes(self.client.get('/api/bookings/?record_status=archived').content)
            Path(destination,'archived-history-list.html').write_bytes(self.client.get('/admin-bookings/?record_status=archived').content)
        before=AccountActivity.objects.count()
        self.assertEqual(self.update(b,'archive').status_code,400)
        self.assertEqual(AccountActivity.objects.count(),before)
        self.assertEqual(self.update(b,'restore').status_code,200)
        b.refresh_from_db();self.assertEqual(b.status,'cancelled')
        self.assertFalse(b.mobile_request.details['archive']['is_archived'])
        self.assertEqual(self.client.get('/api/bookings/').json()['total'],1)
        self.assertEqual(list(FacilityPayment.objects.filter(booking=b).values()),payments)
        for kind in ('booking_cancelled','booking_archived','booking_restored'):
            self.assertEqual(AccountActivity.objects.filter(activity_type=kind,metadata__booking_id=b.pk).count(),1)

    def test_archive_is_permission_scoped_and_does_not_reopen_completed_or_active_bookings(self):
        b=self.create()
        for status in ('pending','approved','completed','rejected'):
            b.status=status;b.save(update_fields=['status'])
            for action in ('archive','restore'):
                self.assertEqual(self.update(b,action).status_code,400)
            b.refresh_from_db();self.assertEqual(b.status,status)
        b.status='cancelled';b.save(update_fields=['status'])
        reader=User.objects.create_user(username='cancelled-history-reader',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['booking']['actions'],[])
        self.assertEqual(self.update(b,'archive').status_code,403)
        self.capture_inspection_flow('cancelled-reader',b)

    def test_cancelled_legacy_read_does_not_fabricate_cancellation_or_inspection(self):
        b=self.create();b.status='cancelled';b.save(update_fields=['status'])
        b.refresh_from_db();original=dict(b.mobile_request.details)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertNotIn('cancel',detail['details'])
        self.assertNotIn('inspections',detail['details'])
        b.refresh_from_db();self.assertEqual(b.mobile_request.details,original)
        self.capture_inspection_flow('cancelled-legacy',b)

    def test_cancellation_status_payment_and_exact_start_boundary(self):
        from .services.booking_workflow import reservation_start, reservation_end
        for status in ('pending','approved'):
            for amount in (Decimal('0'),Decimal('500'),Decimal('2000')):
                with self.subTest(status=status,paid=amount):
                    b=self.create();b.status=status;b.save()
                    if amount:
                        FacilityPayment.objects.create(id=f'PAY-CANCEL-{status}-{amount}',booking=b,
                            payment_status='paid',paid_amount=amount,official_receipt_no='OR-CANCEL',paid_at=timezone.now())
                    before=list(FacilityPayment.objects.filter(booking=b).values())
                    start=reservation_start(b);finish=reservation_end(b)
                    assert start is not None and finish is not None
                    for instant in (start,start+timedelta(seconds=1),finish+timedelta(seconds=1)):
                        with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=instant):
                            detail=self.client.get(f'/api/bookings/{b.pk}/').json()
                            self.assertFalse(detail['booking']['cancellation']['eligible'])
                            self.assertNotIn('cancel',detail['booking']['actions'])
                            result=self.update(b,'cancel',reason='Too late')
                            self.assertEqual(result.status_code,400)
                            self.assertIn('already started',result.json()['error'])
                        b.refresh_from_db();self.assertEqual(b.status,status)
                    with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=start-timedelta(microseconds=1)):
                        self.assertIn('cancel',self.client.get(f'/api/bookings/{b.pk}/').json()['booking']['actions'])
                        result=self.update(b,'cancel',reason='Client requested cancellation before use')
                        self.assertEqual(result.status_code,200,result.content)
                    b.refresh_from_db();self.assertEqual(b.status,'cancelled')
                    self.assertEqual(list(FacilityPayment.objects.filter(booking=b).values()),before)
                    self.assertEqual(AccountActivity.objects.filter(activity_type='booking_cancelled',metadata__booking_id=b.pk).count(),1)

    def test_cancellation_rejects_terminal_and_unknown_start_without_writes(self):
        b=self.create()
        for status in ('completed','cancelled','rejected'):
            b.status=status;b.save()
            self.assertEqual(self.update(b,'cancel',reason='Invalid terminal cancellation').status_code,400)
        b.status='pending';b.start_time=None;b.save()
        result=self.update(b,'cancel',reason='Unknown start')
        self.assertEqual(result.status_code,400)
        self.assertIn('valid reservation start',result.json()['error'])
        self.assertEqual(AccountActivity.objects.filter(activity_type='booking_cancelled').count(),0)

    def test_cancellation_room_start_uses_saved_checkin_clock_and_manila(self):
        from zoneinfo import ZoneInfo
        from .services.booking_workflow import cancellation_readiness
        b=self.create();b.booking_date=None;b.start_time=None;b.check_in_date=self.day;b.check_out_date=self.day+timedelta(days=1);b.save()
        sidecar=b.mobile_request;sidecar.details['check_in_time']='14:00';sidecar.save()
        start=timezone.make_aware(datetime.combine(self.day,datetime.min.time().replace(hour=14)),ZoneInfo('Asia/Manila'))
        with timezone.override('America/New_York'):
            with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=start-timedelta(seconds=1)):
                self.assertTrue(cancellation_readiness(b)['eligible'])
            with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=start):
                self.assertFalse(cancellation_readiness(b)['eligible'])
        sidecar.details['check_in_time']='';sidecar.save();b.refresh_from_db()
        self.assertFalse(cancellation_readiness(b)['eligible'])

    def test_pagination_filters_and_service_schedule_exclusion(self):
        for i in range(23): Booking.objects.create(id=f'PAGE-{i:02}',facility=self.facility,purpose='Test',status='pending')
        Booking.objects.create(id='BLOCK',facility=self.facility,purpose='[class]',status='approved')
        service=Facility.objects.create(id='SERVICE-ONLY',facility_name='Analysis',facility_type='food_analysis',booking_mode='service')
        service_booking=Booking.objects.create(id='SERVICE-BOOKING',facility=service,user=self.user,status='pending')
        page=self.client.get('/api/bookings/?page=2').json()
        self.assertEqual((page['total'],len(page['bookings'])),(23,3))
        self.assertEqual(self.client.get('/api/bookings/?q=PAGE-01').json()['total'],1)
        self.assertEqual(self.client.get(f'/api/bookings/{service_booking.pk}/').status_code,404)
        auth={'HTTP_AUTHORIZATION':'Bearer '+mobile_chat_token(self.user)}
        self.assertEqual(self.client.get(f'/api/mobile/bookings/{service_booking.pk}/',**auth).status_code,404)
        self.assertEqual(self.client.get('/api/mobile/bookings/',**auth).json()['bookings'],[])

    def test_structured_discount_verification(self):
        self.facility.workflow_config={'discount_rules':[{'eligible_client_type':'student','discount_type':'percentage',
            'discount_value':'20','applies_to':'rental_fee','active':True}]};self.facility.save()
        data={**self.data,'discount_index':0,'verification_method':'','discount_reason':'Not sufficient'}
        self.assertEqual(self.post('/api/bookings/preview/',data).status_code,400)
        self.assertEqual(self.post('/api/bookings/preview/',{**data,'verification_method':'Student ID'}).json()['quote']['total_amount'],'1600.00')
        self.assertEqual(self.post('/api/bookings/preview/',{**data,'verification_method':'Student ID','verification_notes':'a'*500}).status_code,200)
        self.assertEqual(self.post('/api/bookings/preview/',{**data,'verification_method':'Other'}).status_code,400)

    def test_empty_kpis_are_visible_and_database_aggregates_once(self):
        from .booking_workflow_views import physical_bookings
        from .services.booking_workflow import booking_kpis
        with self.assertNumQueries(1):
            totals=booking_kpis(physical_bookings())
        self.assertEqual(totals,{'total':0,'pending':0,'upcoming':0,'unpaid':0})
        page=self.client.get('/admin-bookings/')
        self.assertEqual(page.context['booking_kpis'],totals)
        self.assertEqual(page.content.decode().count('data-booking-kpi='),4)
        self.assertNotContains(self.client.get('/admin-calendar/'),'data-booking-kpi=')

    def test_kpi_status_payment_and_scope_matrix(self):
        manual=self.create()
        for state in ('pending','completed','cancelled','rejected'):
            row=Booking.objects.create(id='KPI-'+state,facility=self.facility,user=self.user,booking_date=self.day,
                start_time='13:00',end_time='17:00',status=state,total_amount=2000)
            if state=='pending':FacilityBookingRequest.objects.create(booking=row,request_key=uuid.uuid4(),details={'source':'mobile'})
        paid=Booking.objects.create(id='KPI-PAID',facility=self.facility,booking_date=self.day,status='approved',total_amount=2000)
        for index,amount in enumerate((500,1500)):
            FacilityPayment.objects.create(id=f'KPI-PAID-{index}',booking=paid,payment_status='paid',paid_amount=amount)
        FacilityPayment.objects.create(id='KPI-FAILED',booking=paid,payment_status='failed',paid_amount=9999)
        partial=Booking.objects.create(id='KPI-PARTIAL',facility=self.facility,booking_date=self.day,status='approved',total_amount=2000)
        FacilityPayment.objects.create(id='KPI-PART-PAY',booking=partial,payment_status='paid',paid_amount=500)
        past=Booking.objects.create(id='KPI-PAST',facility=self.facility,booking_date=timezone.localdate()-timedelta(days=1),status='approved',total_amount=100)
        FacilityPayment.objects.create(id='KPI-PAST-PAY',booking=past,payment_status='paid',paid_amount=100)
        pending_paid=Booking.objects.create(id='KPI-PENDING-PAID',facility=self.facility,booking_date=self.day,status='pending',total_amount=100)
        FacilityPayment.objects.create(id='KPI-PENDING-PAY',booking=pending_paid,payment_status='paid',paid_amount=100)
        Booking.objects.create(id='KPI-BLOCK',facility=self.facility,purpose='[class]',status='approved')
        for index,kind in enumerate(('food_analysis','training_kitchen','lease_space')):
            service=Facility.objects.create(id=f'KPI-SERVICE-{index}',facility_name=kind,facility_type=kind,booking_mode='service')
            Booking.objects.create(id=f'KPI-SERVICE-BOOKING-{index}',facility=service,status='pending')
        totals=self.client.get('/api/bookings/').json()['kpis']
        self.assertEqual(totals,{'total':9,'pending':2,'upcoming':1,'unpaid':2})
        for key,expected in (('pending',{'KPI-pending','KPI-PENDING-PAID'}),('upcoming',{'KPI-PAID'}),('unpaid',{manual.pk,partial.pk})):
            response=self.client.get('/api/bookings/',{'kpi':key}).json()
            self.assertEqual({row['id'] for row in response['bookings']},expected)
            self.assertEqual(response['kpis'],totals,'Cards count the full authorized scope, not a page/filter subset')

    def test_upcoming_uses_slot_end_not_start_and_stay_checkout_time(self):
        from datetime import datetime,time
        from .booking_workflow_views import physical_bookings
        from .services.booking_workflow import booking_kpis,filter_booking_kpi
        today=timezone.localdate();now=timezone.make_aware(datetime.combine(today,time(12)))
        expected=set()
        for name,day,end,active in (('active',today,'13:00',True),('future',today,'17:00',True),
            ('ended',today,'12:00',False),('past',today-timedelta(days=1),'17:00',False),('unknown-end',today,None,False)):
            row=Booking.objects.create(id='KPI-SLOT-'+name,facility=self.facility,booking_date=day,start_time='08:00',end_time=end,status='approved',total_amount=100)
            FacilityPayment.objects.create(id='KP-PAY-'+name,booking=row,payment_status='paid',paid_amount=100)
            if active:expected.add(row.pk)
        hostel=Facility.objects.create(id='KPI-HOSTEL',facility_name='Test Hostel',facility_type='hostel',booking_mode='room',workflow_config={'check_out_time':'14:00'})
        for name,day,details,active in (('next-day',today+timedelta(days=1),{},True),
            ('active-stay',today,{'check_out_time':'14:00'},True),('ended-stay',today,{'check_out_time':'12:00'},False),
            ('legacy-config',today,{},True),('snapshot-clock',today,{'workflow_snapshot':{'check_out_time':'13:00'}},True),
            ('no-snapshot-clock',today,{'workflow_snapshot':{}},False),('bad-clock',today,{'check_out_time':'not a time'},False)):
            row=Booking.objects.create(id='KPI-STAY-'+name,facility=hostel,check_in_date=today-timedelta(days=2),check_out_date=day,status='approved',total_amount=100)
            FacilityBookingRequest.objects.create(booking=row,request_key=uuid.uuid4(),details=details)
            FacilityPayment.objects.create(id='KP-STAY-PAY-'+name,booking=row,payment_status='paid',paid_amount=100)
            if active:expected.add(row.pk)
        result=booking_kpis(physical_bookings(),now)
        self.assertEqual(result['upcoming'],len(expected))
        self.assertEqual(set(filter_booking_kpi(physical_bookings(),'upcoming',now).values_list('pk',flat=True)),expected)

    def test_kpi_filter_preserves_search_facility_and_pagination(self):
        for index in range(24):Booking.objects.create(id=f'KPI-PAGE-{index:02}',facility=self.facility,status='pending')
        result=self.client.get('/api/bookings/',{'kpi':'pending','status':'pending','facility':self.facility.pk,'page':2}).json()
        self.assertEqual((result['total'],len(result['bookings']),result['page']),(24,4,2))
        self.assertEqual((result['start_index'],result['end_index']),(21,24))
        result=self.client.get('/api/bookings/',{'kpi':'pending','facility':self.facility.pk,'q':'KPI-PAGE-01'}).json()
        self.assertEqual((result['total'],result['kpis']['pending']),(1,24))
        self.assertEqual((result['start_index'],result['end_index']),(1,1))
        empty=self.client.get('/api/bookings/',{'q':'does-not-match-any-booking'}).json()
        self.assertEqual((empty['total'],empty['start_index'],empty['end_index']),(0,0,0))
        self.assertEqual(self.client.get('/api/bookings/',{'kpi':'unknown'}).json()['total'],24)
        page=self.client.get('/admin-bookings/',{'kpi':'pending','facility':self.facility.pk,'page':2})
        self.assertEqual((len(page.context['booking_requests']),page.context['booking_page']),(4,2))

    def test_kpi_permissions_are_identical_to_bookings_access(self):
        self.create()
        market=User.objects.create_user(username='kpi-market',role='Marketplace Admin',is_staff=True)
        sync_user_admin_permissions(market);self.client.force_login(market)
        self.assertEqual(self.client.get('/api/bookings/').status_code,403)
        self.client.logout();self.assertEqual(self.client.get('/api/bookings/').status_code,401)
        reader=User.objects.create_user(username='kpi-reader',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        result=self.client.get('/api/bookings/').json()
        self.assertEqual(result['kpis']['total'],1);self.assertEqual(result['bookings'][0]['actions'],[])

    def test_zero_cost_requires_a_recorded_payment_for_reserved_mapping(self):
        row=Booking.objects.create(id='KPI-FREE',facility=self.facility,booking_date=self.day,status='approved',total_amount=0)
        self.assertEqual(self.client.get('/api/bookings/').json()['kpis']['unpaid'],1)
        FacilityPayment.objects.create(id='KPI-FREE-OR',booking=row,payment_status='paid',paid_amount=0)
        result=self.client.get('/api/bookings/').json()['kpis']
        self.assertEqual((result['upcoming'],result['unpaid']),(1,0))

    def test_payment_positive_amount_required_and_terminal_states_rejected(self):
        b=self.create()
        values={'action':'payment','payment_method':'Cash','amount_paid':'2000',
            'official_receipt_no':'OR-VALIDATION','paid_at':timezone.now().isoformat()}
        for changes in ({'amount_paid':'0'},{'amount_paid':'-1'},{'amount_paid':'2000.001'},
                        {'amount_paid':'Infinity'},{'amount_paid':'2001'},{'paid_at':''},
                        {'paid_at':(timezone.now()+timedelta(days=1)).isoformat()}):
            with self.subTest(changes=changes):
                self.assertEqual(self.post(f'/api/bookings/{b.pk}/update/',{**values,**changes}).status_code,400)
        for state in ('pending','rejected','cancelled','completed'):
            b.status=state;b.save(update_fields=['status'])
            self.assertEqual(self.post(f'/api/bookings/{b.pk}/update/',values).status_code,400)
        self.assertEqual(self.post('/api/bookings/DOES-NOT-EXIST/update/',values).status_code,404)
        self.assertFalse(FacilityPayment.objects.exists())
        b.status='approved';b.total_amount=0;b.save(update_fields=['status','total_amount'])
        response=self.post(f'/api/bookings/{b.pk}/update/',{**values,'amount_paid':'0'})
        self.assertEqual(response.status_code,400)
        self.assertIn('greater than zero',response.json()['error'])

    def test_payment_receipt_view_download_and_history_are_private(self):
        from PIL import Image
        b=self.create()
        destination=os.environ.get('PAYMENT_REVIEW_DIR')
        def capture(name):
            if destination:
                root=Path(destination);root.mkdir(parents=True,exist_ok=True)
                root.joinpath(name+'.json').write_bytes(self.client.get(f'/api/bookings/{b.pk}/').content)
                root.joinpath(name+'.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
        capture('unpaid')
        image=BytesIO();Image.new('RGB',(2,2),'white').save(image,format='PNG')
        receipt={'name':'cashier.png','type':'image/png','data':base64.b64encode(image.getvalue()).decode()}
        self.assertEqual(self.payment(b,attachment=receipt,notes='Verified cashier receipt').status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        attachment=detail['payments'][0]['receipt_attachment']
        count=AccountActivity.objects.filter(metadata__booking_id=b.pk).count()
        for url,disposition in ((attachment['url'],'attachment'),(attachment['view_url'],'inline')):
            response=self.client.get(url)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.content,image.getvalue())
            self.assertTrue(response['Content-Disposition'].startswith(disposition+';'))
            self.assertEqual(response['Content-Type'],'image/png')
            self.assertEqual(response['Cache-Control'],'private, no-store')
            self.assertEqual(response['X-Content-Type-Options'],'nosniff')
        self.assertEqual(AccountActivity.objects.filter(metadata__booking_id=b.pk).count(),count)
        capture('paid')
        b.refresh_from_db();sidecar=b.mobile_request
        paid_record=sidecar.details['payment_records'][detail['payments'][0]['id']]
        paid_record['attachment']=None;sidecar.save(update_fields=['details']);capture('paid-no-receipt')
        paid_record['attachment']=receipt;sidecar.save(update_fields=['details'])
        failed=FacilityPayment.objects.create(id='FP-HISTORIC-FAILED',booking=b,paid_amount='99',
            payment_status=FacilityPayment.PAYMENT_FAILED,official_receipt_no='OLD-FAILED',paid_at=timezone.now())
        sidecar.details['payment_records'][failed.pk]={'method':'Cash','by':{'id':self.admin.pk,'name':self.admin.get_full_name() or self.admin.username},
            'notes':'Recorded historical failure','attachment':None}
        sidecar.save(update_fields=['details'])
        multiple=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(len(multiple['payments']),2)
        self.assertEqual(Decimal(multiple['booking']['paid_amount']),Decimal('2000'))
        self.assertEqual(Decimal(multiple['booking']['total_amount']),Decimal('2000'))
        self.assertEqual(Decimal(multiple['booking']['amount_due']),0)
        self.assertEqual(multiple['booking']['payment_status'],'paid')
        capture('multiple')
        viewer=User.objects.create_user(username='receipt-reader',is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(viewer);capture('readonly')
        self.assertEqual(self.client.get(attachment['view_url']).status_code,200)
        self.assertEqual(self.payment(b).status_code,403)
        other=Booking.objects.create(id='RECEIPT-OTHER',facility=self.facility,status='approved')
        self.assertEqual(self.client.get(attachment['view_url'].replace(str(b.pk),str(other.pk))).status_code,404)
        self.client.logout()
        self.assertEqual(self.client.get(attachment['url']).status_code,401)
        self.assertEqual(self.client.get(attachment['view_url']).status_code,401)

    def test_receipt_inline_rejects_legacy_active_content(self):
        b=self.create();self.assertEqual(self.payment(b).status_code,200)
        b.refresh_from_db();sidecar=b.mobile_request;key=b.payments.get().pk
        sidecar.details['payment_records'][key]['attachment']={'name':'legacy.html','type':'text/html',
            'data':base64.b64encode(b'<script>unexpected()</script>').decode()}
        sidecar.save(update_fields=['details'])
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertIsNone(detail['payments'][0]['receipt_attachment']['view_url'])
        response=self.client.get(f'/api/bookings/{b.pk}/attachments/{key}/?inline=1')
        self.assertEqual(response.status_code,200)
        self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
        self.assertEqual(response['X-Content-Type-Options'],'nosniff')

    def test_payment_recorder_and_private_receipt_details_are_authoritative(self):
        b=self.create()
        attachment={'name':'cashier.pdf','type':'application/pdf',
            'data':base64.b64encode(b'%PDF-1.4\nexternal cashier receipt').decode()}
        response=self.update(b,'payment',payment_method='Cash',amount_paid='2000',
            official_receipt_no='OR-EVIDENCE',paid_at=timezone.now().isoformat(),
            payment_recorder='Forged Admin',amount_due='1',notes='Verified external receipt',attachment=attachment)
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['message'],'Payment recorded successfully.')
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['recording_user']['id'],self.admin.pk)
        record=detail['payments'][0]
        self.assertEqual(record['by']['id'],self.admin.pk)
        self.assertNotEqual(record['by']['name'],'Forged Admin')
        self.assertEqual(Decimal(record['amount']),Decimal('2000'))
        self.assertEqual(record['receipt_attachment']['name'],'cashier.pdf')
        self.assertNotIn('data',json.dumps(record))
        self.assertEqual(self.client.get(record['receipt_attachment']['url']).content,b'%PDF-1.4\nexternal cashier receipt')
        self.assertTrue(AccountActivity.objects.filter(activity_type='facility_payment_recorded',metadata__booking_id=b.pk).exists())
        viewer=User.objects.create_user(username='payment-proof-viewer',is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(viewer)
        self.assertIsNone(self.client.get(f'/api/bookings/{b.pk}/').json()['recording_user'])
        self.assertEqual(self.payment(b).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(record['receipt_attachment']['url']).status_code,401)

    def test_cashier_permission_is_independent_of_manage_and_approve(self):
        b=self.create()
        cashier=User.objects.create_user(username='custom-cashier',is_staff=True)
        cashier.user_permissions.add(Permission.objects.get(codename='can_record_facility_payment',content_type__app_label='accounts'))
        self.client.force_login(cashier)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual(detail['booking']['actions'],['payment'])
        self.assertEqual(detail['recording_user']['id'],cashier.pk)
        self.assertEqual(self.payment(b).status_code,200)
        b.refresh_from_db()
        self.assertEqual(next(iter(b.mobile_request.details['payment_records'].values()))['by']['id'],cashier.pk)
        self.assertEqual(self.update(b,'cancel',reason='No permission').status_code,403)

    def test_payment_philippine_past_current_future_times(self):
        # 06:00 UTC is 14:00 Philippine time. 13:00 local must not mean 13:00 UTC.
        now=datetime(2026,10,14,6,0,tzinfo=datetime_timezone.utc)
        for index,(value,expected,hour) in enumerate((
            ('2026-10-14T13:00',200,5),('2026-10-14T14:00',200,6),('2026-10-14T14:01',400,None))):
            with self.subTest(value=value):
                self.data['date']=str(self.day+timedelta(days=index))
                b=self.create()
                with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=now):
                    response=self.update(b,'payment',payment_method='Cash',amount_paid='2000',
                        official_receipt_no=f'OR-LOCAL-{index}',paid_at=value)
                self.assertEqual(response.status_code,expected,response.content)
                if expected==200:
                    payment=b.payments.get()
                    self.assertEqual(payment.paid_at.astimezone(datetime_timezone.utc),now.replace(hour=hour))
                    self.assertEqual(response.json()['booking']['status_label'],'Reserved / Confirmed')
                else:
                    self.assertEqual(response.json()['error'],'Payment date and time cannot be in the future.')
                    self.assertFalse(b.payments.exists())

    def test_shared_timestamp_preserves_offsets_and_uses_campus_default(self):
        from .services.booking_workflow import timestamp
        now=datetime(2026,10,14,6,0,tzinfo=datetime_timezone.utc)
        with patch('modules.facilities.services.booking_workflow.timezone.now',return_value=now), timezone.override('UTC'):
            for value in ('2026-10-14T13:00','2026-10-14T13:00+08:00','2026-10-14T05:00Z'):
                self.assertEqual(timestamp(value,'payment date/time').astimezone(datetime_timezone.utc),now.replace(hour=5))
            self.assertEqual(timestamp('2026-10-14T14:00','payment date/time').astimezone(datetime_timezone.utc),now)
            with self.assertRaisesMessage(ValidationError,'Enter a valid payment date/time.'):
                timestamp('not-a-date','payment date/time')

    def test_accommodation_payment_uses_saved_quote_including_deposit(self):
        self.facility.facility_type,self.facility.booking_mode,self.facility.price_type='hostel','room','night'
        self.facility.workflow_config={'check_in_time':'14:00','check_out_time':'12:00',
            'damage_deposit_applicable':True,'damage_deposit':{'type':'fixed','value':'100'}}
        self.facility.save()
        room=Room.objects.create(id=uuid.uuid4(),facility=self.facility,room_name='Payment Room',capacity=3)
        self.data={**self.data,'room_id':str(room.pk),'attendees':2,'adults':2,'children':0,
            'check_in_date':str(self.day),'check_out_date':str(self.day+timedelta(days=2))}
        b=self.create();quote=dict(b.mobile_request.details['quote'])
        response=self.update(b,'payment',payment_method='Cash',amount_paid=str(b.total_amount),
            official_receipt_no='OR-HOSTEL',paid_at=timezone.now().isoformat())
        self.assertEqual(response.status_code,200,response.content)
        self.assertEqual(response.json()['booking']['payment_status'],'paid')
        self.assertEqual(response.json()['booking']['status_label'],'Reserved / Confirmed')
        b.refresh_from_db()
        self.assertEqual(b.mobile_request.details['quote'],quote)
        self.assertEqual(Decimal(quote['deposit_amount']),Decimal('100'))
        self.assertEqual(b.payments.get().paid_amount,b.total_amount)

    def test_full_detail_page_reuses_api_payload_and_protects_access(self):
        b=self.create()
        api=self.client.get(f'/api/bookings/{b.pk}/').json()
        page=self.client.get(f'/admin-bookings/{b.pk}/')
        self.assertEqual(page.status_code,200)
        self.assertTemplateUsed(page,'facilities/pages/admin_booking_details.html')
        self.assertContains(page,'>Booking Slip</button>')
        self.assertEqual(api['documents'][0]['title'],'Booking Slip')
        assert page.context is not None
        self.assertEqual(page.context['booking_detail'],api)
        self.assertEqual(page['Cache-Control'],'private, no-store')
        for tab in ('Overview','BookingForm','JobOrder','Payment','Inspection','Activity'):
            self.assertContains(page,f'id="bkTab{tab}"')
        self.assertNotContains(page,'bkTabDocuments')
        self.assertNotContains(page,'bkBookingDetailsModal')
        listing=self.client.get('/admin-bookings/')
        self.assertNotContains(listing,'bkBookingDetailsModal')
        self.assertNotContains(listing,'bkTabOverview')
        self.assertRedirects(self.client.get('/admin-bookings/',{'booking':b.pk}),f'/admin-bookings/{b.pk}/')
        self.assertEqual(self.client.get('/admin-bookings/UNKNOWN/').status_code,404)
        reader=User.objects.create_user(username='page-reader',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        readonly=self.client.get(f'/admin-bookings/{b.pk}/')
        self.assertEqual(readonly.status_code,200)
        assert readonly.context is not None
        self.assertEqual(readonly.context['booking_detail']['booking']['actions'],[])
        denied=User.objects.create_user(username='page-no-grant',is_staff=True)
        self.client.force_login(denied)
        self.assertEqual(self.client.get(f'/admin-bookings/{b.pk}/').status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(f'/admin-bookings/{b.pk}/').status_code,401)

    def test_detail_documents_keep_existing_files_with_correct_sections(self):
        self.facility.workflow_config={'requires_pre_use_inspection':True};self.facility.save()
        b=self.create()
        attachment={'name':'evidence.pdf','type':'application/pdf','data':base64.b64encode(b'%PDF-1.4\nevidence').decode()}
        self.assertEqual(self.update(b,'job_order',service_requested='Court rental').status_code,200)
        self.assertEqual(self.update(b,'inspection',kind='pre',inspector_id=self.admin.pk,condition='Good Condition',
            inspected_at=timezone.now().isoformat(),attachment=attachment).status_code,200)
        self.assertEqual(self.update(b,'document',title='Legacy supporting upload',attachment=attachment).status_code,200)
        self.assertEqual(self.payment(b,attachment=attachment).status_code,200)
        detail=self.client.get(f'/api/bookings/{b.pk}/').json()
        self.assertEqual({d['section'] for d in detail['documents']},{'BookingForm','JobOrder','Inspection','Payment'})
        self.assertEqual(len([d for d in detail['documents'] if d['section']=='Inspection']),2)
        for doc in detail['documents']:
            self.assertEqual(self.client.get(doc['url']).status_code,200)
        self.assertNotIn('attachment',detail['details']['inspections']['pre'])
        self.assertTrue(all('code' in event for event in detail['activity']))
        destination=os.environ.get('BOOKING_REVIEW_DIR')
        if destination:
            root=Path(destination);root.mkdir(parents=True,exist_ok=True)
            root.joinpath('inspection-detail.json').write_bytes(self.client.get(f'/api/bookings/{b.pk}/').content)
            root.joinpath('inspection-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
        service=Facility.objects.create(id='PAGE-SERVICE',facility_type='food_analysis',booking_mode='service')
        other=Booking.objects.create(id='PAGE-SERVICE-BOOKING',facility=service,status='approved')
        self.assertEqual(self.client.get(f'/admin-bookings/{other.pk}/').status_code,404)

    def test_full_page_and_legacy_redirect_preserve_tab_authentication(self):
        from accounts.admin_tab_auth import create_admin_tab_token
        b=self.create()
        token=create_admin_tab_token(self.admin)
        browser=Client(enforce_csrf_checks=True)
        page=browser.get(f'/admin-bookings/{b.pk}/',{'__at':token})
        self.assertEqual(page.status_code,200)
        self.assertNotIn('sessionid',browser.cookies)
        redirected=browser.get('/admin-bookings/',{'booking':b.pk,'__at':token})
        self.assertRedirects(redirected,f'/admin-bookings/{b.pk}/?__at={token}')
        api=browser.get(f'/api/bookings/{b.pk}/',HTTP_X_ADMIN_TAB_TOKEN=token)
        self.assertEqual(api.json()['booking']['id'],b.pk)
        self.assertEqual(browser.get(f'/admin-bookings/{b.pk}/',{'__at':'invalid'}).status_code,401)
        self.assertEqual(browser.post(f'/api/bookings/{b.pk}/update/',
            json.dumps({'action':'cancel','reason':'Test'}),content_type='application/json',
            HTTP_X_ADMIN_TAB_TOKEN=token).status_code,403)
        b.refresh_from_db();self.assertEqual(b.status,'approved')

    def test_slip_export_browser_configuration_failure_keeps_print_available(self):
        from django.test import override_settings
        b=self.create()
        with override_settings(BOOKING_PDF_BROWSER_BINARY='campushub-missing-pdf-browser'):
            response=self.client.get(f'/api/bookings/{b.pk}/documents/slip/?format=pdf')
        self.assertEqual(response.status_code,503)
        self.assertIn('BOOKING_PDF_BROWSER_BINARY',response.json()['error'])
        self.assertEqual(response['Cache-Control'],'private, no-store')
        self.assertEqual(self.client.get(f'/admin-bookings/{b.pk}/slip/').status_code,200)

    def test_slip_export_render_failures_cleanup_without_changing_booking(self):
        import subprocess
        b=self.create();saved=dict(b.mobile_request.details)
        def invalid_pdf(command, **kwargs):
            output=next(value.split('=',1)[1] for value in command if value.startswith('--print-to-pdf='))
            Path(output).write_bytes(b'not a PDF')
        for failure in (subprocess.TimeoutExpired('test browser',30),invalid_pdf):
            with self.subTest(failure=type(failure).__name__):
                with patch('modules.facilities.services.booking_slip_pdf.subprocess.run',side_effect=failure) as process:
                    response=self.client.get(f'/api/bookings/{b.pk}/documents/slip/?format=pdf')
                self.assertEqual(response.status_code,503)
                self.assertEqual(response['Cache-Control'],'private, no-store')
                command=process.call_args.args[0]
                output=Path(next(value.split('=',1)[1] for value in command if value.startswith('--print-to-pdf=')))
                self.assertFalse(output.parent.exists(),'Disposable HTML/PDF/profile cleaned up')
                b.refresh_from_db();self.assertEqual(b.mobile_request.details,saved)

    def test_official_slip_maps_mobile_saved_data_and_shared_roles(self):
        from .services.booking_slip import booking_slip_data, slip_values
        from pypdf import PdfReader
        from io import BytesIO
        mobile=Client()
        data={**self.data,'request_key':str(uuid.uuid4()),'full_name':'Mobile Requestor',
            'email':'mobile@example.edu','contact_number':'09171234567','event_name':'Sports Day',
            'organization':'Student Council','notes':'Setup before event','additional_requirements':['Chairs','Sound System','Others'],
            'other_requirements':'Extension cable'}
        created=mobile.post('/api/mobile/bookings/',json.dumps(data),content_type='application/json',
            HTTP_AUTHORIZATION='Bearer '+mobile_chat_token(self.user))
        self.assertEqual(created.status_code,201,created.content)
        b=Booking.objects.get(pk=created.json()['booking']['id'])
        saved=dict(b.mobile_request.details);before=Booking.objects.count()
        fields=dict(slip_values(booking_slip_data(b)))
        for key,value in [('Name of Requestor','Mobile Requestor'),('Name of Event / Activity','Sports Day'),
            ('Nature of Event','Training event'),('Start Time','1:00 PM'),('End Time','5:00 PM'),
            ('Tables and Chairs','Selected'),('Sound System','Selected'),('Hotel Function Hall','Not selected')]:
            self.assertEqual(fields[key],value)
        self.assertNotIn('Payment Status',fields)
        self.assertEqual(fields['Official Receipt No.'],'Not recorded')
        self.facility.rate=9999;self.facility.save()
        self.assertEqual(dict(slip_values(booking_slip_data(b)))['Total Amount'],'PHP 2,000.00')
        api=self.client.get(f'/api/bookings/{b.pk}/').json()
        html=self.client.get(f'/admin-bookings/{b.pk}/slip/')
        for value in ('UNIVERSITY OF SCIENCE AND TECHNOLOGY','Sports Day','Extension cable','Requested By'):
            self.assertContains(html,value);self.assertIn(value,api['booking_form_html'])
        self.assertContains(html,'OF SOUTHERN<br>PHILIPPINES')
        pdf=self.client.get(f'/api/bookings/{b.pk}/documents/slip/?format=pdf')
        self.assertEqual(pdf.status_code,200)
        text=' '.join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
        self.assertEqual([line.strip() for line in text.splitlines()[:2]],
            ['UNIVERSITY OF SCIENCE AND TECHNOLOGY OF SOUTHERN','PHILIPPINES'])
        for value in ('UNIVERSITY OF SCIENCE AND TECHNOLOGY','Sports Day','Extension cable','PHP 2,000.00','Requested By'):
            self.assertIn(value,text)
        self.assertNotContains(html, '<dt>Name</dt>')
        self.assertNotContains(html, '<dt>Signature</dt>')
        self.assertIn('Signature:', text)
        self.assertIn('Name:', text)
        self.assertIn('Mobile Requestor', text)
        self.assertContains(html, 'Requested By:')
        slip=booking_slip_data(b)
        for section in (slip['sections'][2],slip['sections'][4]):
            self.assertEqual(sum(c['label']=='Others' for c in section['choices']),1)
            self.assertFalse(any(f['label']=='Others' for f in section['fields']))
        self.assertEqual(slip['sections'][4]['choices'][-1]['value'],'Extension cable')
        self.assertEqual(slip['sections'][2]['choices'][-1]['value'],'')
        self.assertEqual(text.count('Others:'),2)
        superuser=User.objects.create_user(username='slip-super',role='Super Admin',is_staff=True,is_superuser=True)
        self.client.force_login(superuser)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['booking_form_html'],api['booking_form_html'])
        b.refresh_from_db();self.assertEqual(b.mobile_request.details,saved);self.assertEqual(Booking.objects.count(),before)
        destination=os.environ.get('BOOKING_REVIEW_DIR')
        if destination:
            root=Path(destination);root.mkdir(parents=True,exist_ok=True)
            root.joinpath('official-slip.html').write_bytes(html.content)
            root.joinpath('official-slip.pdf').write_bytes(pdf.content)
            root.joinpath('official-detail.json').write_text(json.dumps(api),encoding='utf-8')
            root.joinpath('official-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)

    def test_rental_other_facility_keeps_name_on_single_checkbox_line(self):
        from .services.booking_slip import booking_slip_data, slip_values
        b=self.create()
        self.facility.facility_type='other';self.facility.facility_name='Training Pavilion';self.facility.save()
        b.refresh_from_db()
        slip=booking_slip_data(b);section=slip['sections'][2]
        self.assertEqual(section['fields'],[])
        other=section['choices'][-1]
        self.assertTrue(other['checked']);self.assertTrue(other['write_in'])
        self.assertEqual(other['value'],self.facility.facility_name)
        self.assertEqual(dict(slip_values(slip))['3. Facility Requested - Other details'],self.facility.facility_name)
        html=self.client.get(f'/admin-bookings/{b.pk}/slip/')
        self.assertContains(html,self.facility.facility_name);self.assertNotContains(html,'<dt>Others</dt>')

    def test_official_slip_payment_history_signatures_escaping_and_access(self):
        from .services.booking_slip import booking_slip_data, slip_values
        from .services.booking_workflow import save_details
        b=self.create();details=dict(b.mobile_request.details)
        details.update(event_name='<script>alert(1)</script>',additional_requirements=['Projector','Others'],other_requirements='Long equipment '+('word '*350),notes='Long note '+('word '*350))
        save_details(b,details)
        self.assertEqual(self.payment(b).status_code,200)
        b.refresh_from_db();slip=booking_slip_data(b);fields=dict(slip_values(slip))
        self.assertEqual(fields['Amount Paid'],'PHP 2,000.00');self.assertEqual(fields['Official Receipt No.'],'OR-WORKFLOW')
        self.assertEqual(slip['signatories'][2]['name'],'Dr. Glorimer L. Clarin')
        self.assertEqual(slip['signatories'][2]['role'],'Acting Campus Director')
        self.assertEqual(slip['signatories'][1]['name'],'Not recorded')
        html=self.client.get(f'/admin-bookings/{b.pk}/slip/')
        self.assertContains(html,'&lt;script&gt;alert(1)&lt;/script&gt;');self.assertNotContains(html,'<script>alert(1)</script>')
        self.assertContains(html,'Reviewed By (Campus Admin / Facility In-Charge):')
        self.assertContains(html,'Approved By:')
        self.assertNotContains(html,'Additional Notes');self.assertNotContains(html,'Long note')
        self.assertEqual(b.mobile_request.details['notes'],details['notes'])
        pdf=self.client.get(f'/api/bookings/{b.pk}/documents/slip/?format=pdf');self.assertEqual(pdf.status_code,200)
        from pypdf import PdfReader
        from io import BytesIO
        text=' '.join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
        self.assertNotIn('Additional Notes',text);self.assertNotIn('Long note',text)
        self.assertIn('Long equipment',text)
        destination=os.environ.get('BOOKING_REVIEW_DIR')
        if destination:Path(destination).joinpath('official-long-slip.pdf').write_bytes(pdf.content)
        reader=User.objects.create_user(username='official-viewer',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(reader)
        self.assertEqual(self.client.get(f'/admin-bookings/{b.pk}/slip/').status_code,200)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/slip/?format=pdf').status_code,200)
        self.client.logout();self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/documents/slip/?format=pdf').status_code,401)

    def test_official_slip_category_accommodation_and_missing_history(self):
        from .services.booking_slip import booking_slip_data, slip_values
        b=self.create()
        self.assertTrue(booking_slip_data(b)['sections'][2]['choices'][0]['checked'])
        self.facility.facility_type='function_hall';self.facility.save();b.refresh_from_db()
        self.assertTrue(booking_slip_data(b)['sections'][2]['choices'][1]['checked'])
        self.facility.facility_type='hostel';self.facility.booking_mode='room';self.facility.price_type='night'
        self.facility.workflow_config={'check_in_time':'14:00','check_out_time':'12:00'};self.facility.save()
        room=Room.objects.create(id=uuid.uuid4(),facility=self.facility,room_name='Official Room',capacity=3)
        self.data={**self.data,'room_id':str(room.pk),'attendees':2,'adults':2,'children':0,
            'check_in_date':str(self.day+timedelta(days=2)),'check_out_date':str(self.day+timedelta(days=4))}
        stay=self.create();slip=booking_slip_data(stay);fields=dict(slip_values(slip))
        self.assertEqual(slip['title'],'Room Accommodation Booking Slip')
        self.assertFalse(slip['rental']);self.assertEqual(fields['Room / Unit'],'Official Room')
        self.assertEqual(fields['Check-in Time'],'2:00 PM');self.assertEqual(fields['Children'],'0')
        self.assertNotIn('Covered Court',fields)
        legacy=Booking.objects.create(id='LEGACY-OFFICIAL-SLIP',facility=self.facility,purpose='Legacy stay',total_amount=100)
        legacy_fields=dict(slip_values(booking_slip_data(legacy)))
        self.assertEqual(legacy_fields['Base Rental Fee'],'Not recorded')
        self.assertEqual(legacy_fields['Official Receipt No.'],'Not recorded')
        self.assertEqual(legacy_fields['Total Amount'],'PHP 100.00')
        pdf=self.client.get(f'/api/bookings/{stay.pk}/documents/slip/?format=pdf');self.assertEqual(pdf.status_code,200)
        destination=os.environ.get('BOOKING_REVIEW_DIR')
        if destination:Path(destination).joinpath('official-accommodation.pdf').write_bytes(pdf.content)

    def test_paper_slip_removes_accounting_extras_and_keeps_real_finances(self):
        from .services.booking_slip import booking_slip_data, slip_values
        self.facility.workflow_config={'damage_deposit_applicable':True,'damage_deposit':{'type':'fixed','value':'100'}}
        self.facility.save();b=self.create()
        fields=dict(slip_values(booking_slip_data(b)))
        self.assertEqual(fields['Facility Fee'],'PHP 2,000.00')
        self.assertEqual(fields['Total Amount'],'PHP 2,000.00')
        self.assertEqual(fields['Equipment Fee'],'Not recorded')
        for extra in ('Remaining Balance','Payment Status','Damage Deposit','Receipt Amount','Duration','Booking Status'):
            self.assertNotIn(extra,fields)
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['booking']['total_amount'],'2100.00')
        paid=self.update(b,'payment',payment_method='Cash',amount_paid='2100.00',official_receipt_no='OR-PAPER',paid_at=timezone.now().isoformat())
        self.assertEqual(paid.status_code,200,paid.content)
        b.refresh_from_db();fields=dict(slip_values(booking_slip_data(b)))
        self.assertEqual(fields['Amount Paid'],'PHP 2,100.00')
        self.assertEqual(fields['Official Receipt No.'],'OR-PAPER')
        self.assertEqual(self.client.get(f'/api/bookings/{b.pk}/').json()['booking']['approved_by'],'workflow-admin')

    def test_paper_signatories_use_configured_officials_not_system_roles(self):
        from django.test import override_settings
        from .services.booking_slip import booking_slip_data
        b=self.create()
        config={'reviewer':{'name':'Assigned Reviewer','title':'Facility In-Charge'},
                'approver':{'name':'Configured Director','title':'Campus Director'}}
        with override_settings(BOOKING_SLIP_SIGNATORIES=config):
            slip=booking_slip_data(b)
            self.assertEqual(slip['signatories'][1]['name'],'Assigned Reviewer')
            self.assertEqual(slip['signatories'][2]['name'],'Configured Director')
            self.assertEqual(slip['signatories'][2]['role'],'Campus Director')
            html=self.client.get(f'/admin-bookings/{b.pk}/slip/')
            self.assertContains(html,'Configured Director');self.assertNotContains(html,'workflow-admin')
            self.assertNotContains(html,'Super Admin')
        with override_settings(BOOKING_SLIP_SIGNATORIES={'reviewer':{},'approver':{}}):
            self.assertEqual(booking_slip_data(b)['signatories'][2]['name'],'Not recorded')
        with override_settings(BOOKING_SLIP_SIGNATORIES={'reviewer':{},'approver':{'name':'Configured Director','title':'Super Admin'}}):
            self.assertEqual(booking_slip_data(b)['signatories'][2]['role'],'Not recorded')

    def test_export_transaction_review(self):
        destination=os.environ.get('BOOKING_REVIEW_DIR')
        if not destination:return
        root=Path(destination);root.mkdir(parents=True,exist_ok=True)
        b=self.create()
        root.joinpath('workflow.html').write_bytes(self.client.get('/admin-bookings/').content)
        root.joinpath('workflow-options.json').write_bytes(self.client.get(f'/api/bookings/facilities/{self.facility.pk}/options/').content)
        root.joinpath('workflow-slots.json').write_bytes(self.client.get(f'/api/mobile/facilities/{self.facility.pk}/availability/',
            {'date':self.day,'booking_id':b.pk}).content)
        root.joinpath('details-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
        root.joinpath('detail.json').write_bytes(self.client.get(f'/api/bookings/{b.pk}/').content)
        root.joinpath('list.json').write_bytes(self.client.get('/api/bookings/').content)
        for key in ('pending','upcoming','unpaid'):
            root.joinpath(f'kpi-{key}.json').write_bytes(self.client.get('/api/bookings/',{'kpi':key}).content)
        self.update(b,'job_order',service_requested='Court rental',specifics='Practice')
        attachment={'name':'reference.pdf','type':'application/pdf','data':base64.b64encode(b'%PDF-1.4\nreference').decode()}
        self.assertEqual(self.update(b,'document',title='Job Order',attachment=attachment).status_code,200)
        root.joinpath('job-order.pdf').write_bytes(self.client.get(f'/api/bookings/{b.pk}/documents/job-order/?format=pdf').content)
        root.joinpath('workflow-slip.pdf').write_bytes(self.client.get(f'/api/bookings/{b.pk}/documents/slip/?format=pdf').content)
        result=self.payment(b,attachment=attachment,notes='External cashier receipt verified')
        root.joinpath('paid-result.json').write_bytes(result.content)
        root.joinpath('paid-detail.json').write_bytes(self.client.get(f'/api/bookings/{b.pk}/').content)
        root.joinpath('paid-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
        root.joinpath('paid-list.json').write_bytes(self.client.get('/api/bookings/').content)
        for key in ('pending','upcoming','unpaid'):
            root.joinpath(f'paid-kpi-{key}.json').write_bytes(self.client.get('/api/bookings/',{'kpi':key}).content)
        viewer=User.objects.create_user(username='workflow-viewer',is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(codename='can_view_bookings',content_type__app_label='accounts'))
        self.client.force_login(viewer)
        root.joinpath('readonly-list.json').write_bytes(self.client.get('/api/bookings/').content)
        root.joinpath('readonly-detail.json').write_bytes(self.client.get(f'/api/bookings/{b.pk}/').content)
        root.joinpath('readonly-page.html').write_bytes(self.client.get(f'/admin-bookings/{b.pk}/').content)
