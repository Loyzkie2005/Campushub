"""Service catalog configuration, with writes confined to the isolated test database."""
import json
import os
from pathlib import Path
from copy import deepcopy
from decimal import Decimal

from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Facility, CampusHubUser, Room, Booking, FacilityPayment, FacilityBookingRequest
from .services.catalog import service_resources_q
from .services.service_configuration import service_document_requirements, SCHEDULING_METHODS


class ServiceConfigurationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        tables=connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser,Facility,Room,Booking,FacilityPayment):
                if model._meta.db_table not in tables:editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.admin=User.objects.create_user(username='service-config-admin',role='Facilities Admin',is_staff=True)
        sync_user_admin_permissions(self.admin);self.client.force_login(self.admin)
        self.data={'catalog_kind':'service','name':'Test Service Configuration','facility_type':'food_analysis',
            'mode':'service','status':'available','price_type':'analysis','location':'','rate':'',
            'workflow_config':{'requires_approval':True,'service':{'job_order_required':True,'soa_required':True,
                'payment_timing':'billing','output_type':'analysis_certificate','sample_acceptance_required':True,
                'availability_enabled':False,'pricing_items':[{'name':'Manually configured test','description':'Actual test fixture','fee':'120.00','active':True}]}},
            'requirements':'Configured submission requirements','terms_conditions':'Configured service terms','images':[]}

    def post(self,data,service=None):
        return self.client.post(f'/api/facilities/{service.pk}/update/' if service else '/api/facilities/create/',
                               json.dumps(data),content_type='application/json')

    def create(self,data=None):
        response=self.post(data or self.data)
        self.assertEqual(response.status_code,201,response.content)
        return Facility.objects.get(pk=response.json()['facility']['id'])

    def test_service_reuses_storage_and_does_not_create_transactions(self):
        service=self.create()
        self.assertTrue(Facility.objects.filter(service_resources_q(),pk=service.pk).exists())
        self.assertEqual(service.workflow_config['service']['pricing_items'][0]['fee'],'120.00')
        self.assertEqual(service.amenities,[]);self.assertEqual(service.capacity,0)
        self.assertFalse(Booking.objects.exists());self.assertFalse(FacilityPayment.objects.exists())
        self.assertTrue(service.workflow_config['service']['soa_required'])
        self.assertEqual(self.client.get('/admin-bookings/').context['booking_requests'],[])
        page=self.client.get('/admin-services/')
        self.assertContains(page,'1 active analysis rate')
        self.assertNotIn(service.pk,{f.pk for f in self.client.get(reverse('admin_facility_page')).context['facilities']})

    def test_validation_is_authoritative_and_atomic(self):
        mutations=[{'name':'   '},{'facility_type':'covered_court'},{'mode':'slot'},{'status':'maintenance'},
                   {'price_type':'hour'},{'price_type':'candidate'}]
        for mutation in mutations:
            self.assertEqual(self.post({**self.data,**mutation}).status_code,400)
        self.assertFalse(Facility.objects.exists())
        for key,val in [('payment_timing',[]),('output_type','bad'),('availability_enabled','yes')]:
            data=deepcopy(self.data);data['workflow_config']['service'][key]=val
            self.assertEqual(self.post(data).status_code,400)

    def test_other_and_custom_fields_require_trimmed_values(self):
        data={**deepcopy(self.data),'facility_type':'other','price_type':'custom'}
        data['workflow_config']['service'].update(payment_timing='custom',output_type='custom')
        self.assertEqual(self.post(data).status_code,400)
        data.update(custom_facility_type='  Custom Service Category  ')
        data['workflow_config']['service'].update(custom_payment_timing='  After review  ',custom_output_type='  Written result  ',custom_pricing_description='  Priced after scope review  ')
        service=self.create(data)
        self.assertEqual(service.custom_facility_type,'Custom Service Category')
        self.assertEqual(service.workflow_config['service']['custom_payment_timing'],'After review')
        self.assertEqual(service.workflow_config['service']['custom_pricing_description'],'Priced after scope review')

    def test_all_supported_rate_methods_and_invalid_money(self):
        for category,methods in [('training_kitchen',['candidate','fixed']),('lease_space',['monthly','sqm','machine_month']),('other',['custom'])]:
            for method in methods:
                data=deepcopy(self.data);data.update(facility_type=category,price_type=method,rate='250.75',mode='lease' if category=='lease_space' else 'assessment',custom_facility_type='Other Category')
                data['workflow_config']['service']['custom_pricing_description']='Configured formula'
                if category=='training_kitchen':data['workflow_config']['service']['scheduling_method']='admin_assigned'
                service=self.create(data)
                self.assertEqual(str(service.rate),'250.75')
        for rate in ('-1','NaN','Infinity','1.234',True):
            self.assertEqual(self.post({**self.data,'price_type':'fixed','rate':rate}).status_code,400)

    def test_analysis_rows_are_single_structure_and_not_duplicated_on_edit(self):
        service=self.create();data=deepcopy(self.data)
        data['workflow_config']['service']['pricing_items'].append({'name':'Second configured analysis','description':'','fee':'0','active':False})
        for attempt in range(2):self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db()
        self.assertEqual(len(service.workflow_config['service']['pricing_items']),2)
        self.assertEqual(Facility.objects.count(),1)
        for items in ([],[{'name':' ','fee':'1','active':True}],data['workflow_config']['service']['pricing_items']*2):
            broken=deepcopy(data);broken['workflow_config']['service']['pricing_items']=items
            self.assertEqual(self.post(broken,service).status_code,400)
        service.refresh_from_db();self.assertEqual(len(service.workflow_config['service']['pricing_items']),2)

    def test_availability_is_optional_validated_and_cleared_when_disabled(self):
        data=deepcopy(self.data);data['workflow_config']['service']['availability_enabled']=True
        self.assertEqual(self.post(data).status_code,400)
        data['workflow_config']['operating_hours']={'monday':{'open':'09:00','close':'08:00'}}
        self.assertEqual(self.post(data).status_code,400)
        from .services.operating_schedule import WEEKDAYS
        data['workflow_config']['operating_hours']={day:None for day in WEEKDAYS}
        response=self.post(data)
        self.assertEqual(response.status_code,400)
        self.assertIn('at least one available day',response.json()['errors']['operating_hours'])
        data['workflow_config']['operating_hours']={day:({'open':'08:00','close':'12:00'} if day=='monday' else None) for day in WEEKDAYS}
        service=self.create(data)
        self.assertEqual(service.workflow_config['operating_hours']['monday']['open'],'08:00')
        data['workflow_config']['service']['availability_enabled']=False
        self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db();self.assertNotIn('operating_hours',service.workflow_config)

    def test_category_switch_clears_hidden_owned_settings_and_preserves_history(self):
        data=deepcopy(self.data);data['workflow_config']['turnaround_information']='Configured duration'
        service=self.create(data);service.workflow_config['unrelated_saved_setting']='Keep';service.save()
        booking=Booking.objects.create(id='SERVICE-HISTORY',facility=service,status='completed',total_amount=120)
        changed=deepcopy(self.data);changed.update(facility_type='training_kitchen',mode='assessment',price_type='candidate',rate='100',capacity=12)
        changed['workflow_config'].update(assessment_service_type='Configured assessment')
        changed['workflow_config']['service']['scheduling_method']='specific_date'
        self.assertEqual(self.post(changed,service).status_code,200)
        service.refresh_from_db();booking.refresh_from_db()
        self.assertEqual(service.capacity,12)
        self.assertNotIn('pricing_items',service.workflow_config['service'])
        self.assertNotIn('sample_acceptance_required',service.workflow_config['service'])
        self.assertNotIn('turnaround_information',service.workflow_config)
        self.assertEqual(service.workflow_config['unrelated_saved_setting'],'Keep')
        self.assertEqual(booking.status,'completed');self.assertEqual(booking.facility_id,service.pk)
        self.assertEqual(Booking.objects.count(),1);self.assertFalse(FacilityPayment.objects.exists())

    def test_leasing_configuration_does_not_require_hours_or_rooms(self):
        data=deepcopy(self.data);data.update(facility_type='lease_space',mode='lease',price_type='monthly',rate='800')
        data['workflow_config']['service'].update(lease_space_types=['canteen','other'],other_lease_space_type='  Configured custom space  ',contract_required=True)
        service=self.create(data)
        self.assertEqual(service.workflow_config['service']['other_lease_space_type'],'Configured custom space')
        self.assertNotIn('operating_hours',service.workflow_config)
        self.assertIsNone(service.rooms_units);self.assertFalse(Room.objects.exists())
        data['workflow_config']['service']['other_lease_space_type']='  '
        self.assertEqual(self.post(data,service).status_code,400)

    def test_partial_existing_api_updates_preserve_configured_service_data(self):
        service=self.create()
        self.assertEqual(self.post({'description':'Updated description','status':'inactive'},service).status_code,200)
        self.assertEqual(self.post({'workflow_config':{'service':{'job_order_required':False}}},service).status_code,200)
        service.refresh_from_db()
        self.assertEqual(service.description,'Updated description')
        self.assertEqual(service.availability_status,'inactive')
        self.assertTrue(service.workflow_config['service']['job_order_required'])
        self.assertTrue(service.workflow_config['service']['soa_required'])
        self.assertEqual(len(service.workflow_config['service']['pricing_items']),1)
        self.assertEqual(service.workflow_config['service']['pricing_items'][0]['fee'],'120.00')
        custom=deepcopy(self.data);custom.update(price_type='custom',rate='')
        custom['workflow_config']['service']['custom_pricing_description']='Based on scope'
        service=self.create(custom)
        self.assertEqual(self.post({'description':'Updated custom service'},service).status_code,200)
        service.refresh_from_db()
        self.assertFalse(service.workflow_config['service']['custom_amount_set'])

    def test_document_controls_are_ignored_and_workflow_defaults_are_server_owned(self):
        for category,mode,expected in [('food_analysis','service',(True,True)),
                ('training_kitchen','assessment',(True,False)),('lease_space','lease',(False,False))]:
            data=deepcopy(self.data)
            data.update(facility_type=category,mode=mode,price_type='fixed',rate='30')
            data['workflow_config']['service'].update(job_order_required='Untrusted input',soa_required=not expected[1])
            if category=='training_kitchen':data['workflow_config']['service']['scheduling_method']='admin_assigned'
            service=self.create(data)
            config=service.workflow_config['service']
            self.assertEqual((config['job_order_required'],config['soa_required']),expected)
            self.assertEqual(service_document_requirements(category,mode),
                {'job_order_required':expected[0],'soa_required':expected[1],'contract_required':category=='lease_space'})
        self.assertFalse(Booking.objects.exists());self.assertFalse(FacilityPayment.objects.exists())
        self.assertFalse(FacilityBookingRequest.objects.exists())

    def test_existing_document_flags_and_transaction_metadata_are_preserved(self):
        import uuid
        service=self.create()
        service.workflow_config['service'].update(job_order_required=False,soa_required=False)
        service.save(update_fields=['workflow_config'])
        booking=Booking.objects.create(id='SERVICE-DOCUMENT-HISTORY',facility=service,status='completed',total_amount=120)
        details={'job_order':{'number':'HISTORICAL-JO'},'statement_of_account':{'number':'HISTORICAL-SOA'}}
        sidecar=FacilityBookingRequest.objects.create(booking=booking,request_key=uuid.uuid4(),details=details)
        data=deepcopy(self.data)
        data['workflow_config']['service'].pop('job_order_required')
        data['workflow_config']['service'].pop('soa_required')
        for ignored in ({},{'job_order_required':True,'soa_required':True}):
            data['workflow_config']['service'].update(ignored)
            self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db();sidecar.refresh_from_db()
        self.assertFalse(service.workflow_config['service']['job_order_required'])
        self.assertFalse(service.workflow_config['service']['soa_required'])
        self.assertEqual(sidecar.details,details)
        self.assertEqual(Booking.objects.count(),1)
        # Effective workflow policy is independent of old compatibility switches.
        self.assertTrue(service_document_requirements(service.facility_type,service.booking_mode)['job_order_required'])

    def test_blank_output_is_unspecified_not_none_and_request_type_is_required(self):
        data=deepcopy(self.data);data['workflow_config']['service'].pop('output_type')
        service=self.create(data)
        self.assertEqual(service.workflow_config['service']['output_type'],'')
        for output in ('','none'):
            data['workflow_config']['service']['output_type']=output
            self.assertEqual(self.post(data,service).status_code,200)
            service.refresh_from_db();self.assertEqual(service.workflow_config['service']['output_type'],output)
        data['mode']=''
        self.assertEqual(self.post(data).status_code,400)
        page=self.client.get('/admin-services/')
        self.assertContains(page,'Select request type')
        self.assertContains(page,'Select result / output type')
        self.assertNotContains(page,'id="serviceJobOrder"')
        self.assertNotContains(page,'id="serviceSOA"')

    def test_unchanged_saved_closed_week_is_preserved_but_new_closed_week_is_rejected(self):
        from .services.operating_schedule import WEEKDAYS
        closed={day:None for day in WEEKDAYS}
        service=self.create()
        service.workflow_config.update(operating_hours=closed)
        service.workflow_config['service']['availability_enabled']=True
        service.save(update_fields=['workflow_config'])
        self.assertEqual(self.post({'description':'Updated saved closed service'},service).status_code,200)
        service.refresh_from_db();self.assertEqual(service.workflow_config['operating_hours'],closed)
        open_hours={**closed,'monday':{'open':'08:00','close':'12:00'}}
        self.assertEqual(self.post({'workflow_config':{'operating_hours':open_hours}},service).status_code,200)
        self.assertEqual(self.post({'workflow_config':{'operating_hours':closed}},service).status_code,400)
        service.refresh_from_db();self.assertEqual(service.workflow_config['operating_hours'],open_hours)

    def test_existing_service_update_preserves_identity_and_legacy_images(self):
        service=Facility.objects.create(id='EXISTING-SERVICE',facility_type='food_analysis',booking_mode='service',
            facility_name='Existing Service',image_url='/media/existing-service.webp',workflow_config={'unrelated':'Keep'},rate=20,price_type='service')
        data=deepcopy(self.data);data.pop('images')
        self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db();self.assertEqual(service.image_url,'/media/existing-service.webp')
        self.assertEqual(service.workflow_config['unrelated'],'Keep')
        self.assertEqual(Facility.objects.count(),1)

    def test_cannot_convert_physical_facility_with_service_payload_or_bypass_permissions(self):
        physical=Facility.objects.create(id='PHYSICAL-SERVICE-TEST',facility_type='covered_court',booking_mode='slot',facility_name='Physical Test')
        self.assertEqual(self.post(self.data,physical).status_code,400)
        physical.refresh_from_db();self.assertEqual(physical.facility_type,'covered_court')
        readonly=User.objects.create_user(username='service-reader',is_staff=True)
        readonly.user_permissions.add(Permission.objects.get(codename='can_view_facilities',content_type__app_label='accounts'))
        self.client.force_login(readonly)
        self.assertEqual(self.client.get('/admin-services/').status_code,200)
        self.assertEqual(self.post(self.data).status_code,302)
        market=User.objects.create_user(username='service-market',role='Marketplace Admin',is_staff=True)
        sync_user_admin_permissions(market);self.client.force_login(market)
        self.assertEqual(self.client.get('/admin-services/').status_code,403)
        self.assertEqual(self.post(self.data).status_code,302)

    def test_lease_contract_policy_is_server_owned_and_legacy_history_is_preserved(self):
        data=deepcopy(self.data)
        data.update(facility_type='lease_space',mode='lease',price_type='monthly',rate='800')
        data['workflow_config']['service'].update(output_type='none',contract_required=False)
        service=self.create(data)
        self.assertTrue(service.workflow_config['service']['contract_required'])
        self.assertEqual(service.workflow_config['service']['output_type'],'none','Output stays editable')
        self.assertTrue(service_document_requirements('lease_space','lease')['contract_required'])
        for ignored in (False,'Untrusted input',None):
            self.assertEqual(self.post({'workflow_config':{'service':{'contract_required':ignored}}},service).status_code,200)
            service.refresh_from_db();self.assertTrue(service.workflow_config['service']['contract_required'])
        service.workflow_config['service']['contract_required']=False
        service.save(update_fields=['workflow_config'])
        booking=Booking.objects.create(id='LEASE-CONTRACT-HISTORY',facility=service,status='completed',total_amount=800)
        self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db();booking.refresh_from_db()
        self.assertFalse(service.workflow_config['service']['contract_required'],'Legacy switch retained as history')
        self.assertTrue(service_document_requirements(service.facility_type,service.booking_mode)['contract_required'])
        self.assertEqual(booking.status,'completed');self.assertEqual(Booking.objects.count(),1)
        self.assertFalse(FacilityPayment.objects.exists());self.assertFalse(FacilityBookingRequest.objects.exists())
        self.assertNotContains(self.client.get('/admin-services/'),'id="serviceContractRequired"')

    def training_payload(self,method='admin_assigned',capacity=''):
        data=deepcopy(self.data)
        data.update(facility_type='training_kitchen',mode='assessment',price_type='candidate',rate='100',capacity=capacity)
        data['workflow_config'].update(assessment_service_type='Configured assessment name')
        data['workflow_config']['service'].update(scheduling_method=method,output_type='assessment_result')
        return data

    def test_training_method_required_and_validated_server_side(self):
        for method in ('',None,'bad',[],True):
            response=self.post(self.training_payload(method))
            self.assertEqual(response.status_code,400)
            self.assertIn('scheduling_method',response.json()['errors'])
        missing=self.training_payload();missing['workflow_config']['service'].pop('scheduling_method')
        self.assertEqual(self.post(missing).status_code,400)
        self.assertFalse(Facility.objects.exists())
        for method in SCHEDULING_METHODS:
            data=self.training_payload(method)
            data['workflow_config']['service']['schedule_required']='Untrusted checkbox input'
            service=self.create(data)
            self.assertEqual(service.workflow_config['service']['scheduling_method'],method)
            self.assertEqual(service.workflow_config['service']['schedule_required'],method!='none')
            self.assertEqual(self.post({'description':'Updated method-preserving description'},service).status_code,200)
            service.refresh_from_db();self.assertEqual(service.workflow_config['service']['scheduling_method'],method)
        self.assertFalse(Booking.objects.exists());self.assertFalse(FacilityPayment.objects.exists())
        self.assertFalse(FacilityBookingRequest.objects.exists())

    def test_candidate_capacity_is_optional_or_positive_whole_number(self):
        for capacity in ('',None,1,'20'):
            service=self.create(self.training_payload(capacity=capacity))
            self.assertEqual(service.capacity,0 if capacity in ('',None) else int(capacity))
            self.assertEqual(self.post({'description':'Partial capacity-preserving edit'},service).status_code,200)
        for capacity in (0,'0',-1,'1.5',True,False,'NaN','Infinity','1000001'):
            response=self.post(self.training_payload(capacity=capacity))
            self.assertEqual(response.status_code,400)
            self.assertIn('candidate_capacity',response.json()['errors'])

    def test_training_scheduling_and_weekly_hours_are_independent(self):
        from .services.operating_schedule import WEEKDAYS
        from .services.calendar import calendar_facilities
        hours={day:({'open':'08:10','close':'17:00'} if day=='monday' else None) for day in WEEKDAYS}
        for method in SCHEDULING_METHODS:
            data=self.training_payload(method,capacity=12)
            data['workflow_config']['service']['availability_enabled']=True
            data['workflow_config']['operating_hours']=hours
            service=self.create(data)
            self.assertEqual(service.workflow_config['service']['scheduling_method'],method)
            self.assertEqual(service.workflow_config['operating_hours'],hours)
            self.assertFalse(calendar_facilities().filter(pk=service.pk).exists())
            data['workflow_config']['service']['availability_enabled']=False
            self.assertEqual(self.post(data,service).status_code,200)
            service.refresh_from_db()
            self.assertNotIn('operating_hours',service.workflow_config)
            self.assertEqual(service.workflow_config['service']['scheduling_method'],method)
        self.assertFalse(Booking.objects.exists());self.assertFalse(FacilityBookingRequest.objects.exists())

    def test_legacy_checkbox_is_preserved_not_guessed_or_editable(self):
        service=self.create(self.training_payload('admin_assigned'))
        service.workflow_config['service'].pop('scheduling_method')
        service.workflow_config['service']['schedule_required']=True
        service.save(update_fields=['workflow_config'])
        self.assertEqual(self.post(self.training_payload(''),service).status_code,400)
        service.refresh_from_db()
        self.assertNotIn('scheduling_method',service.workflow_config['service'])
        data=self.training_payload('none');data['workflow_config']['service']['schedule_required']=False
        self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db()
        self.assertEqual(service.workflow_config['service']['scheduling_method'],'none')
        self.assertTrue(service.workflow_config['service']['schedule_required'])

    def test_other_categories_ignore_stale_method_and_clear_training_config(self):
        service=self.create(self.training_payload('specific_date',capacity=15))
        booking=Booking.objects.create(id='TRAINING-SCHEDULING-HISTORY',facility=service,status='completed',total_amount=100)
        for category,mode in [('food_analysis','service'),('lease_space','lease'),('other','service')]:
            data=deepcopy(self.data)
            data.update(facility_type=category,mode=mode,price_type='fixed',rate='100',custom_facility_type='Configured custom category')
            data['workflow_config']['service']['scheduling_method']=['Stale hidden input']
            self.assertEqual(self.post(data,service).status_code,200)
            service.refresh_from_db();booking.refresh_from_db()
            self.assertNotIn('scheduling_method',service.workflow_config['service'])
            self.assertNotIn('assessment_service_type',service.workflow_config)
            self.assertEqual(service.capacity,0)
            self.assertTrue(service.workflow_config['service']['schedule_required'])
            self.assertEqual(booking.status,'completed')
        self.assertEqual(Booking.objects.count(),1)

    def test_export_editor_fixtures(self):
        destination=os.environ.get('SERVICE_REVIEW_DIR')
        if not destination:return
        root=Path(destination);root.mkdir(parents=True,exist_ok=True)
        service=self.create()
        import base64
        image=Path(__file__).resolve().parents[3]/'static/assets/img/icon.png'
        service.image_url='data:image/png;base64,'+base64.b64encode(image.read_bytes()).decode()
        service.save(update_fields=['image_url'])
        root.joinpath('configured-services.html').write_bytes(self.client.get('/admin-services/').content)
        from api.views import serialize_facility
        root.joinpath('service-saved.json').write_text(json.dumps({'facility':serialize_facility(service)}),encoding='utf-8')
        reader=User.objects.create_user(username='service-fixture-reader',is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='can_view_facilities',content_type__app_label='accounts'))
        self.client.force_login(reader)
        root.joinpath('configured-services-readonly.html').write_bytes(self.client.get('/admin-services/').content)
        self.client.force_login(self.admin)
        training=self.create(self.training_payload('admin_assigned',capacity=18))
        root.joinpath('training-service-saved.json').write_text(json.dumps({'facility':serialize_facility(training)}),encoding='utf-8')
        root.joinpath('configured-training-services.html').write_bytes(self.client.get('/admin-services/').content)

    def test_analysis_charging_basis_round_trips_and_invalid_basis_is_rejected(self):
        data=deepcopy(self.data)
        data['workflow_config']['service']['pricing_items'][0]['charging_basis']='sample'
        service=self.create(data)
        self.assertEqual(service.workflow_config['service']['pricing_items'][0]['charging_basis'],'sample')
        data['workflow_config']['service']['pricing_items'][0]['charging_basis']='hour'
        self.assertEqual(self.post(data,service).status_code,400)
        service.refresh_from_db()
        self.assertEqual(service.workflow_config['service']['pricing_items'][0]['charging_basis'],'sample')

    def test_assessment_dates_are_service_config_not_facility_bookings(self):
        data=self.training_payload('specific_date',capacity=12)
        dates=[{'date':'2026-11-20','start':'08:00','end':'12:00'}, {'date':'2026-11-21','start':'','end':''}]
        data['workflow_config']['service']['assessment_dates']=dates
        service=self.create(data)
        self.assertEqual(service.workflow_config['service']['assessment_dates'],dates)
        self.assertFalse(Booking.objects.exists())
        for bad in ([dates[0],dates[0]],[{'date':'invalid'}],[{'date':'2026-11-20','start':'12:00','end':'08:00'}]):
            data['workflow_config']['service']['assessment_dates']=bad
            self.assertEqual(self.post(data,service).status_code,400)
        data['workflow_config']['service'].update(scheduling_method='none',assessment_dates=dates)
        self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db();self.assertNotIn('assessment_dates',service.workflow_config['service'])

    def test_lease_space_rates_areas_utilities_and_term_rates_are_configurable(self):
        data=deepcopy(self.data);data.update(facility_type='lease_space',mode='lease',price_type='term',rate='')
        config=data['workflow_config']['service']
        config.update(term_rates={'regular':'1200','midyear':'600'},lease_space_types=['stall','vendo'],
            lease_space_details={'stall':{'available_area':'6','standard_area':'3','pricing_method':'term',
                'regular_term_rate':'900','midyear_rate':'450','water_charge':'150','electricity_arrangement':'Separate meter'},
                'vendo':{'pricing_method':'machine_month','rate':'200','internet_arrangement':'Renter supplies connection'}})
        service=self.create(data);saved=service.workflow_config['service']
        self.assertEqual(service.rate,Decimal('1200'));self.assertEqual(saved['term_rates']['midyear'],'600')
        self.assertEqual(saved['lease_space_details']['stall']['standard_area'],'3')
        self.assertEqual(saved['lease_space_details']['vendo']['rate'],'200')
        self.assertNotIn('operating_hours',service.workflow_config)
        self.assertFalse(Room.objects.exists());self.assertFalse(Booking.objects.exists())
        config['lease_space_details']['stall']['water_charge']='-1'
        self.assertEqual(self.post(data,service).status_code,400)
        service.refresh_from_db();self.assertEqual(service.workflow_config['service']['lease_space_details']['stall']['water_charge'],'150')
        config['lease_space_details']['stall']['water_charge']='150'
        config['lease_space_types']=['vendo']
        self.assertEqual(self.post(data,service).status_code,200)
        service.refresh_from_db();self.assertNotIn('stall',service.workflow_config['service']['lease_space_details'])

    def test_service_status_pricing_audit_and_archive_preserve_request_history(self):
        from accounts.models import AccountActivity
        service=self.create()
        booking=Booking.objects.create(id='SERVICE-FINAL-HISTORY',facility=service,status='completed',total_amount=120)
        payment=FacilityPayment.objects.create(id='SERVICE-FINAL-PAYMENT',booking=booking,paid_amount=120,payment_status='paid')
        self.assertTrue(AccountActivity.objects.filter(module='Services',activity_type='service_added',metadata__facility_id=service.pk).exists())
        for status in ('unavailable','inactive','available'):
            self.assertEqual(self.post({'catalog_kind':'service','status':status},service).status_code,200)
        before=AccountActivity.objects.count()
        self.assertEqual(self.post({'status':'available'},service).status_code,200)
        self.assertEqual(AccountActivity.objects.count(),before)
        changed=deepcopy(self.data);changed['workflow_config']['service']['pricing_items'][0]['fee']='125'
        self.assertEqual(self.post(changed,service).status_code,200)
        self.assertTrue(AccountActivity.objects.filter(module='Services',activity_type='service_pricing_updated',metadata__facility_id=service.pk).exists())
        self.assertEqual(self.client.post(f'/api/facilities/{service.pk}/archive/').status_code,200)
        service.refresh_from_db();self.assertTrue(service.is_archived)
        self.assertEqual(self.post({'status':'available'},service).status_code,400)
        self.assertEqual(self.client.post(f'/api/facilities/{service.pk}/delete/').status_code,405)
        self.assertEqual(self.client.post(f'/api/facilities/{service.pk}/restore/').status_code,200)
        booking.refresh_from_db();payment.refresh_from_db()
        self.assertEqual(booking.status,'completed');self.assertEqual(str(payment.paid_amount),'120.00')

    def test_filter_labels_scoped_requests_and_configured_lease_editor_fixtures(self):
        service=self.create();other=self.create(self.training_payload('admin_assigned'))
        for target,key in ((service,'FILTER-LAB'),(other,'FILTER-ASSESS')):
            Booking.objects.create(id=key,facility=target,status='pending')
        response=self.client.get('/admin-service-requests/',{'service':service.pk})
        self.assertEqual([item.pk for item in response.context['request_page']],['FILTER-LAB'])
        self.assertContains(response,'name="service"')
        page=self.client.get('/admin-services/')
        for field in ('facilitySearchInput','facilityTypeFilter','facilityStatusFilter','facilityBookingModeFilter','facilityArchiveFilter'):
            self.assertContains(page,f'for="{field}"')
        destination=os.environ.get('SERVICE_REVIEW_DIR')
        if destination:
            lease=deepcopy(self.data);lease.update(name='Configured Lease Offering',facility_type='lease_space',mode='lease',price_type='monthly',rate='750')
            lease['workflow_config']['service'].update(lease_space_types=['stall','vendo'],lease_space_details={
                'stall':{'available_area':'6','standard_area':'3','water_charge':'150','electricity_arrangement':'Separate meter'},
                'vendo':{'pricing_method':'machine_month','rate':'200','internet_arrangement':'Renter supplies connection'}})
            resource=self.create(lease)
            from api.views import serialize_facility
            root=Path(destination);root.mkdir(parents=True,exist_ok=True)
            root.joinpath('configured-lease-services.html').write_bytes(self.client.get('/admin-services/').content)
            root.joinpath('lease-service-saved.json').write_text(json.dumps({'facility':serialize_facility(resource)}),encoding='utf-8')
            root.joinpath('service-requests.html').write_bytes(response.content)
