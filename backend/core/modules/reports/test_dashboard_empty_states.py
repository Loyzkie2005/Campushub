"""Initial empty presentation over isolated ORM records; no changes to application data."""
from datetime import date, datetime, time
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import tests as fixtures
from accounts.models import AccountActivity
from api.models import Booking, Facility, MarketplaceOrder, Product


class EmptyComponentTests(SimpleTestCase):
    def test_text_is_escaped_and_icon_is_decorative(self):
        html = render_to_string('dashboard/partials/empty_state.html', {
            'title': '<script>not markup</script>', 'description': 'No requests.', 'icon': 'trend',
        })
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('aria-hidden="true" focusable="false"', html)
        self.assertNotIn('<button', html)

    def test_bundle_failures_are_not_empty_successes(self):
        for template, context in [
            ('bundle_suggestions.html', {'bundle_analysis': {'monitor_error': True}}),
            ('bundle_activity.html', {'activity': {'error': True}}),
        ]:
            html = render_to_string('marketplace/partials/'+template, {'global_dashboard': True, **context})
            self.assertIn('role="alert"', html)
            self.assertNotIn('ch-dashboard-empty', html)

    def test_shared_domain_partials_keep_their_existing_presentation(self):
        html = render_to_string('dashboard/partials/attention_required.html', {
            'global_dashboard': False, 'attention_required': {'items': []},
        })
        self.assertIn('No urgent items require attention.', html)
        self.assertNotIn('dashboard-attention-error', html)
        self.assertNotIn('ch-dashboard-empty', html)
        html = render_to_string('dashboard/partials/low_stock_card.html', {
            'global_dashboard': False, 'dashboard_low_stock': {'products': [], 'state': 'ready'},
        })
        self.assertNotIn('ch-dashboard-empty', html)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DashboardEmptyStatesTests(fixtures.DedicatedDomainDashboardTests):
    today = date(2026, 10, 4)

    def setUp(self):
        super().setUp()
        if self._testMethodName in fixtures.DedicatedDomainDashboardTests.__dict__:
            return
        self.client.force_login(self.super_admin)
        Booking.objects.all().delete()
        MarketplaceOrder.objects.all().delete()
        AccountActivity.objects.all().delete()
        Product.objects.update(stock=100)
        self.service = Facility.objects.create(id='EMPTY-SERVICE', facility_name='Isolated laboratory', booking_mode='service')

    def test_initial_zero_one_multiple_and_export(self):
        target = os.environ.get('EMPTY_REVIEW_DIR')
        for count, state in [(0, 'empty'), (1, 'one'), (2, 'multiple')]:
            if count:
                stamp = timezone.make_aware(datetime.combine(self.today, time(12)))
                MarketplaceOrder.objects.create(product=self.prod_approved, product_name=self.prod_approved.name,
                    quantity=1, unit_price=100, total_price=100, status='completed', payment_status='paid', completed_at=stamp, paid_at=stamp)
                for resource in (self.fac_court, self.service):
                    booking = Booking.objects.create(id=f'EMPTY-{resource.pk}-{count}', facility=resource,
                        user=self.ch_user, status='approved', booking_date=date(2099, 1, count), start_time=time(9), end_time=time(10))
                    Booking.objects.filter(pk=booking.pk).update(created_at=stamp)
                event = AccountActivity.objects.create(account_source='admin', account_id=self.super_admin.pk,
                    activity_type='service_updated', activity='Updated', module='Services', result='success')
                AccountActivity.objects.filter(pk=event.pk).update(created_at=stamp)
                Product.objects.filter(pk=self.prod_low.pk).update(stock=1)
            with patch('django.utils.timezone.localdate', return_value=self.today):
                page = self.client.get(reverse('admin_dashboard_page'), {'period': 'today'})
                payload = self.client.get(reverse('admin_dashboard_api'), {'period': 'today'}).json()
            self.assertEqual(page.status_code, 200)
            html = page.content.decode()
            for title in ('No Sales Data Yet', 'No Top-Selling Products Yet', 'No Recent Orders', 'No Inventory Alerts',
                          'No Booking Data Yet',
                          'No Booked Facilities Yet', 'No Upcoming Reservations', 'No Facility Attention Needed',
                          'No Service Request Data Yet', 'No Service Request Activity Yet', 'No Recent Service Requests',
                          'No Service Attention Needed', 'No Items Require Attention', 'No Recent System Activities'):
                self.assertIn(title, html)
            self.assertEqual(payload['marketplace']['completed_orders'], count)
            self.assertEqual(len(payload['operations']['recent_orders']), count)
            self.assertEqual(payload['facilities']['booking_overview']['total'], count)
            self.assertEqual(len(payload['facilities']['upcoming_reservations']), count)
            self.assertEqual(payload['executive']['services']['total_requests'], count)
            self.assertEqual(len(payload['executive']['activities']), count)
            if not count:
                self.assertIn('data-has-sales="false" hidden', html)
                self.assertIn('data-products-content hidden', html)
                self.assertIn('class="facility-booking-chart-wrap" hidden', html)
                self.assertIn('data-service-trend-wrap hidden', html)
                self.assertIn('data-service-recent-wrap tabindex="0" role="region" aria-label="Recent service requests table" hidden', html)
                self.assertIn('class="low-stock-table" hidden', html)
                self.assertIn('aria-labelledby="recentOrdersTitle" hidden', html)
            if target:
                directory = Path(target); directory.mkdir(parents=True, exist_ok=True)
                (directory/f'{state}.html').write_bytes(page.content)
                (directory/f'{state}.json').write_text(json.dumps(payload), encoding='utf-8')
