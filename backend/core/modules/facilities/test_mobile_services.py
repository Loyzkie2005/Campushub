"""Catalog-only mobile Services: actual records, public allowlist, no intake writes."""
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from api.models import CampusHubUser, Facility, Room


class MobileServiceCatalogTests(TestCase):
    @classmethod
    def setUpClass(cls):
        existing = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room):
                if model._meta.db_table not in existing:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.lab = Facility.objects.create(id='M-LAB', facility_name='Actual laboratory',
            facility_type='food_analysis', booking_mode='service', price_type='analysis',
            workflow_config={'internal_staff_notes': 'NEVER PUBLIC', 'service': {
                'sample_acceptance_required': True,
                'pricing_items': [{'name': 'Moisture', 'fee': '450', 'active': True, 'charging_basis': 'sample'},
                                  {'name': 'Hidden test', 'fee': '99', 'active': False}]}})
        self.assessment = Facility.objects.create(id='M-ASSESS', facility_name='Actual assessment',
            facility_type='training_kitchen', booking_mode='assessment')
        self.lease = Facility.objects.create(id='M-LEASE', facility_name='Actual lease',
            facility_type='lease_space', booking_mode='lease')
        Facility.objects.create(id='M-COURT', facility_name='Physical Court', facility_type='covered_court', booking_mode='slot')

    def test_only_active_unarchived_services_and_no_n_plus_one(self):
        for status in ('unavailable', 'maintenance', 'inactive', 'reserved', 'occupied'):
            Facility.objects.create(id='M-'+status, facility_name=status, facility_type='food_analysis', availability_status=status)
        Facility.objects.create(id='M-ARCHIVE', facility_name='Archived', facility_type='food_analysis', is_archived=True)
        with self.assertNumQueries(1):
            response = self.client.get(reverse('mobile_service_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({r['id'] for r in response.json()['services']}, {'M-LAB', 'M-ASSESS', 'M-LEASE'})

    def test_public_detail_uses_real_pricing_and_excludes_internal_configuration(self):
        response = self.client.get(reverse('mobile_service_detail', args=[self.lab.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()['service']
        self.assertEqual(data['name'], self.lab.facility_name)
        self.assertFalse(data['online_requests_available'])
        self.assertContains(response, 'Moisture')
        self.assertContains(response, '450')
        self.assertNotContains(response, 'Hidden test')
        self.assertNotContains(response, 'NEVER PUBLIC')
        self.assertNotIn('workflow_config', data)

    def test_unavailable_archived_physical_and_missing_details_fail_closed(self):
        self.lab.availability_status = 'inactive'
        self.lab.save()
        self.assessment.is_archived = True
        self.assessment.save()
        for key in (self.lab.pk, self.assessment.pk, 'M-COURT', 'missing'):
            self.assertEqual(self.client.get(reverse('mobile_service_detail', args=[key])).status_code, 404)

    def test_empty_read_only_and_legacy_service_mode(self):
        Facility.objects.filter(facility_type__in=['food_analysis', 'training_kitchen', 'lease_space']).update(is_archived=True)
        self.assertEqual(self.client.get(reverse('mobile_service_list')).json()['services'], [])
        Facility.objects.create(id='M-LEGACY', facility_name='Legacy actual service', facility_type='other', booking_mode='direct')
        self.assertEqual([r['id'] for r in self.client.get(reverse('mobile_service_list')).json()['services']], ['M-LEGACY'])
        self.assertEqual(self.client.post(reverse('mobile_service_list'), {}).status_code, 405)
        self.assertEqual(self.client.post(reverse('mobile_service_detail', args=['M-LEGACY']), {}).status_code, 405)

    def test_optional_physical_filter_preserves_original_default_contract(self):
        self.assertEqual({r['id'] for r in self.client.get(reverse('facilities_list'), {'resource_type': 'facility'}).json()['facilities']}, {'M-COURT'})
        self.assertIn('M-LAB', {r['id'] for r in self.client.get(reverse('facilities_list')).json()['facilities']})
