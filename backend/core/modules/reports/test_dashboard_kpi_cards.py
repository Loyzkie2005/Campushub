"""System Overview layout reads the canonical snapshot without mining on GET."""
import json
import os
from pathlib import Path
import re
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from api.models import MarketplaceOrder, Product


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SystemOverviewCardsTests(TestCase):
    keys = ['total_users', 'active_sellers', 'total_products', 'total_orders',
            'marketplace_revenue', 'total_facilities', 'total_bookings', 'pending_approvals']

    def setUp(self):
        self.root = User.objects.create_superuser(username='kpi-root', email='kpi@example.test', password='test')
        self.client.force_login(self.root)

    def test_card_order_real_destinations_and_no_render_time_mining(self):
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions',
                   side_effect=AssertionError('No Apriori during page rendering')):
            response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(re.findall(r'data-dashboard-kpi="([^"]+)"', html), self.keys)
        links = re.findall(r'class="dashboard-stat-card h-100 dashboard-kpi-link" href="([^"]+)"', html)
        routes = ['admin_users_page', 'admin_sellers_page', 'admin_products_page', 'admin_orders_page',
                  'admin_marketplace_analytics_page', 'admin_facility_page', 'admin_bookings_page']
        self.assertEqual(links, [reverse(route) for route in routes])
        for link in links:
            with self.subTest(link=link):
                self.assertEqual(self.client.get(link).status_code, 200)
        self.assertContains(response, 'id="dashboardKpiStale"')
        self.assertContains(response, 'class="marketplace-recommendation-counts"', count=1)
        self.assertNotContains(response, 'id="dashboardSystemStatus"')

    def test_initial_values_match_api_and_large_currency_is_not_truncated(self):
        product = Product.objects.create(seller=self.root, name='Isolated KPI item', price=10,
                                         stock=5, approval_status=Product.STATUS_APPROVED)
        # A large aggregate must use legal individual order amounts.
        MarketplaceOrder.objects.bulk_create([MarketplaceOrder(product=product, product_name=product.name,
            quantity=1, unit_price='99999999.99', total_price='99999999.99',
            status='completed', payment_status='paid') for _ in range(130)])
        response = self.client.get(reverse('admin_dashboard_page'))
        payload = self.client.get(reverse('admin_dashboard_api')).json()
        html = response.content.decode()
        values = dict(re.findall(r'data-dashboard-kpi="([^"]+)">([^<]+)</strong>', html))
        for key in self.keys:
            displayed = values[key].replace('&#8369;', '').replace(',', '')
            self.assertEqual(float(displayed), payload['kpis'][key]['value'])
        self.assertContains(response, '&#8369;12,999,999,998.70')
        self.assertEqual(payload['kpis']['total_users']['value'], 1)  # Includes the admin account.
        directory = os.environ.get('KPI_REVIEW_DIR')
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / 'dashboard.html').write_bytes(response.content)
            (path / 'payload.json').write_text(json.dumps(payload), encoding='utf-8')

    def test_failed_snapshot_returns_retryable_error_without_fake_values(self):
        with patch('modules.reports.views.build_dashboard_data', side_effect=DatabaseError('private database detail')):
            response = self.client.get(reverse('admin_dashboard_api'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'error': 'Dashboard data is unavailable. Please retry.'})
        self.assertNotIn('kpis', response.json())
        self.assertNotContains(response, 'private database detail', status_code=503)
