"""Regression coverage for the dedicated read-only Facility Admin dashboard."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace
import os
from pathlib import Path
import uuid
from unittest.mock import patch

from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from accounts.models import AccountActivity
from api.models import Booking, Facility, FacilityBookingRequest, FacilityPayment
from .dashboard_facilities import facility_admin_dashboard


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class FacilityAdminDashboardTests(fixtures.DedicatedDomainDashboardTests):
    def data(self, **params):
        return facility_admin_dashboard(RequestFactory().get('/', params), self.facilities_admin)

    def booking(self, key, **kwargs):
        defaults = dict(facility=self.fac_court, user=self.ch_user, status=Booking.STATUS_PENDING,
                        booking_date=timezone.localdate() + timedelta(days=3), start_time=time(9), end_time=time(11))
        defaults.update(kwargs)
        return Booking.objects.create(id=key, **defaults)

    def service(self):
        return Facility.objects.create(id='dashboard-service', facility_name='Food Analysis',
            facility_type=Facility.TYPE_FOOD_ANALYSIS, booking_mode='service')

    def test_physical_classification_archives_and_pending_queue(self):
        service = self.service()
        self.booking('service-request', facility=service)
        self.booking('old-pending')
        self.booking('new-pending')
        Booking.objects.filter(pk='old-pending').update(created_at=timezone.now()-timedelta(days=2))
        archived = self.booking('archived-pending')
        FacilityBookingRequest.objects.create(booking=archived, request_key=uuid.uuid4(), details={'archive':{'is_archived':True}})
        self.booking('class-block', purpose='[class] Academic use')
        Facility.objects.create(id='retired-facility', facility_name='Archived room', is_archived=True)
        data = self.data()
        self.assertEqual(data['total_facilities'], 1)
        self.assertEqual(data['pending_bookings'], 2)
        self.assertEqual([r['id'] for r in data['pending_requests']], ['old-pending', 'new-pending'])
        self.assertEqual(data['pending_requests'][0]['url'], reverse('admin_booking_details_page', args=['old-pending']))
        self.assertEqual(data['facilities_list'][0]['status'], 'Open for Booking')

    def test_paid_positive_receipted_collections_only(self):
        service_booking = self.booking('service-pay', facility=self.service(), status=Booking.STATUS_APPROVED)
        cancelled = self.booking('cancelled-pay', status=Booking.STATUS_CANCELLED)
        retired = Facility.objects.create(id='retired-paid', facility_name='Retired physical facility', is_archived=True)
        historical = self.booking('historical-pay', facility=retired, status=Booking.STATUS_COMPLETED)
        values = [('one','100', 'paid','OR-100',self.booking_upcoming),
                  ('partial','40', 'paid','OR-040',self.booking_upcoming),
                  ('unpaid','800', 'unpaid','OR-unpaid',self.booking_upcoming),
                  ('failed','800', 'failed','OR-failed',self.booking_upcoming),
                  ('no-or','800', 'paid',None,self.booking_upcoming),
                  ('blank-or','800', 'paid','  ',self.booking_upcoming),
                  ('service','800', 'paid','OR-service',service_booking),
                  ('cancelled','800', 'paid','OR-cancelled',cancelled),
                  ('zero','0', 'paid','OR-zero',self.booking_upcoming),
                  ('historical','60','paid','OR-history',historical)]
        for key, amount, status, receipt, booking in values:
            FacilityPayment.objects.create(id='pay-'+key, booking=booking, paid_amount=Decimal(amount),
                payment_status=status, official_receipt_no=receipt, paid_at=timezone.now())
        result = self.data()['payment_stats']
        self.assertEqual(result['total_collected'], '200.00')
        self.assertEqual({r['or_number'] for r in result['recent_receipts']}, {'OR-100','OR-040','OR-history'})
        self.assertTrue(all(r['url'].endswith('?tab=Payment') for r in result['recent_receipts']))

    def test_upcoming_dates_and_room_stays(self):
        today = timezone.localdate()
        self.booking('ended-today', status=Booking.STATUS_APPROVED, booking_date=today, start_time=time(8), end_time=time(9))
        self.booking('later-today', status=Booking.STATUS_APPROVED, booking_date=today, start_time=time(14), end_time=time(15))
        self.booking('future-stay', status=Booking.STATUS_APPROVED, booking_date=None,
            check_in_date=today+timedelta(days=1), check_out_date=today+timedelta(days=2), start_time=None, end_time=None)
        with patch('django.utils.timezone.now', return_value=timezone.make_aware(datetime.combine(today,time(12)))):
            data = self.data()
        self.assertEqual(data['upcoming_reservations_count'], 3)
        self.assertEqual([r['id'] for r in data['upcoming_reservations']], ['later-today','future-stay',self.booking_upcoming.pk])
        self.assertIn('Check-out', data['upcoming_reservations'][1]['time'])

    def test_real_daily_weekly_monthly_buckets_and_ajax(self):
        today = timezone.localdate()
        for key, days in [('week',5), ('quarter',40), ('year',300)]:
            booking = self.booking('trend-'+key)
            Booking.objects.filter(pk=booking.pk).update(created_at=timezone.make_aware(datetime.combine(today-timedelta(days=days), time(12))))
        self.booking('ignored-service', facility=self.service())
        self.booking('ignored-block', purpose='[maintenance] Repaint')
        self.assertEqual(sum(self.data(booking_grouping='daily')['booking_chart']['values']), 2)
        self.assertEqual(sum(self.data(booking_grouping='weekly')['booking_chart']['values']), 3)
        self.assertEqual(sum(self.data(booking_grouping='monthly')['booking_chart']['values']), 4)
        self.assertEqual(self.data(booking_grouping='invalid')['booking_grouping'], 'daily')
        self.client.force_login(self.facilities_admin)
        response = self.client.get(reverse('admin_dashboard_page'), {'booking_grouping':'weekly'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['booking_grouping'], 'weekly')
        self.assertEqual(len(response.json()['booking_chart']['labels']), 12)

    def test_schedule_projection_includes_real_blocks_and_operational_states(self):
        self.booking('overlap', status=Booking.STATUS_APPROVED, booking_date=self.booking_upcoming.booking_date)
        self.booking('maintenance-block', purpose='[maintenance] Repaint', status=Booking.STATUS_APPROVED,
            booking_date=self.booking_upcoming.booking_date, start_time=time(11), end_time=time(12))
        Facility.objects.create(id='maintenance', facility_name='Maintenance room', availability_status=Facility.STATUS_MAINTENANCE)
        Facility.objects.create(id='offline', facility_name='Closed hall', availability_status=Facility.STATUS_UNAVAILABLE)
        schedule = self.data()['schedule_overview']
        self.assertEqual(schedule['detected_conflicts'], 2)
        self.assertEqual(schedule['maintenance_count'], 1)
        self.assertEqual(schedule['unavailable_count'], 1)
        self.assertTrue(schedule['has_issues'])

    def test_existing_activity_scope_and_empty_states(self):
        for module, facility, message in [('Facilities',self.fac_court,'Maintenance status updated'),
                                           ('Facility Bookings',self.service(),'Service submitted'),
                                           ('Marketplace',self.fac_court,'Product changed')]:
            AccountActivity.objects.create(account_source='admin', result='success', activity_type='updated',
                activity=message, module=module, metadata={'facility_id':facility.pk})
        self.assertEqual([r['message'] for r in self.data()['activities']], ['Maintenance status updated'])
        Booking.objects.all().delete()
        Facility.objects.all().delete()
        data = self.data()
        self.assertEqual(data['total_facilities'], 0)
        self.assertEqual(data['booking_chart']['values'], [0]*7)
        self.assertFalse(data['schedule_overview']['has_issues'])

    def test_template_workflow_links_and_permissions(self):
        self.booking('review-me')
        self.client.force_login(self.facilities_admin)
        response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '?action=add-reservation')
        bookings = self.client.get(reverse('admin_bookings_page'))
        self.assertContains(bookings, 'id="bkOpenReservationBtn"')
        self.assertContains(response, '?action=upload-schedule')
        self.assertContains(response, reverse('admin_booking_details_page', args=['review-me']))
        self.assertContains(response, 'Review Queue')
        self.assertContains(response, 'No verified facility receipts recorded yet.')
        self.assertNotContains(response, 'Marketplace Sales')
        # Rendered, isolated test fixtures for browser QA; never live dashboard data.
        if preview := os.environ.get('FACILITY_DASHBOARD_PREVIEW_DIR'):
            directory = Path(preview)
            directory.mkdir(parents=True, exist_ok=True)
            (directory/'fixture-dashboard.html').write_bytes(response.content)
            for page, name in [('admin_bookings_page', 'fixture-bookings.html'), ('admin_calendar_page', 'fixture-calendar.html')]:
                rendered = self.client.get(reverse(page))
                self.assertEqual(rendered.status_code, 200)
                (directory/name).write_bytes(rendered.content)
            review = self.client.get(reverse('admin_booking_details_page', args=['review-me']))
            self.assertEqual(review.status_code, 200)
        result = facility_admin_dashboard(RequestFactory().get('/'), SimpleNamespace(has_perm=lambda code:False))
        self.assertFalse(result['can_view_payments'])
        self.client.logout()
        self.assertEqual(self.client.get(reverse('admin_dashboard_page')).status_code, 302)

