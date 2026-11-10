"""Saved synthetic dashboard display; transactions and live recommendations stay separate."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AccountActivity, User
from api.models import BundleRecommendation, Product, MarketplaceOrder
from modules.marketplace.tests import test_bundle_monitoring as fixtures
from modules.marketplace.services.bundle_suggestions import (
    dashboard_synthetic_preview, dashboard_bundle_suggestions, execute_synthetic_research)


class DashboardSyntheticPreviewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        from api.models import CampusHubUser, Room, Booking, FacilityPayment, FacilityFeedback
        tables = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Room, Booking, FacilityPayment, FacilityFeedback):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
                    tables.add(model._meta.db_table)
        super().setUpClass()

    def setUp(self):
        fixtures.BundleMonitoringTests.setUp(self)
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.report = Path(directory.name) / 'saved-demo.json'
        options = override_settings(CAMPUSHUB_SELLER_DEMO_REPORT_PATH=str(self.report))
        options.enable()
        self.addCleanup(options.disable)

    def counts(self):
        return [model.objects.count() for model in (Product, MarketplaceOrder, BundleRecommendation, AccountActivity)]

    def card(self, response):
        html = response.content.decode() if hasattr(response, 'content') else response
        start = html.index('<section class="dash-card bundle-dss marketplace-recommendation-summary dashboard-bundle-demo"')
        return html[start:html.index('</section>', start)]

    def source_panel(self, response, source):
        html = self.card(response)
        start = html.index('<div id="bundleSyntheticPanel"' if source == 'synthetic' else '<div id="bundleLivePanel"')
        end = html.index('<div id="bundleLivePanel"') if source == 'synthetic' else len(html)
        return html[start:end]

    def test_both_roles_read_identical_saved_product_only_results_without_mining(self):
        self.assertEqual(dashboard_synthetic_preview(self.manager)['state'], 'not_generated')
        before = self.counts()
        saved = execute_synthetic_research(self.root)
        cache.clear()  # Durable product-only results survive research cache expiry.
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', side_effect=AssertionError('GET cannot mine')):
            root = dashboard_synthetic_preview(self.root)
            manager = dashboard_synthetic_preview(self.manager)
        self.assertEqual(root, manager)
        self.assertEqual(root['state'], 'ready')
        self.assertEqual(len(root['rows']), len(saved['result']['rows']))
        for public, original in zip(root['rows'], saved['result']['rows']):
            self.assertEqual(public['seller'], original['seller'])
            self.assertEqual([p['name'] for p in public['products']], [p['name'] for p in original['products']])
            self.assertTrue(all(p['demo'] and p['image_url'].startswith('/static/marketplace/demo/bundles/')
                                for p in public['products']))
        for forbidden in ('support', 'confidence', 'lift', 'transaction_count', 'item_count', 'rule_count', 'metrics'):
            self.assertNotIn(forbidden, json.dumps(root))
        self.assertEqual(before, self.counts())

    def test_dashboard_pages_refresh_and_actual_projection_share_one_card_and_preserve_live_data(self):
        execute_synthetic_research(self.root)
        before = self.counts()
        panels = []
        directory = os.environ.get('DASHBOARD_DEMO_REVIEW_DIR')
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', side_effect=AssertionError('Dashboard cannot mine')):
            for label, user in [('super', self.root), ('marketplace', self.manager)]:
                self.client.force_login(user)
                response = self.client.get(reverse('admin_dashboard_page'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'marketplace/js/bundle_suggestions.js?v=20261110-dashboard-tabs')
                panel = self.card(response)
                panels.append(panel)
                self.assertIn('Demo Only', panel)
                self.assertIn('Synthetic Demo', panel)
                self.assertIn('Live Recommendations', panel)
                self.assertIn('Sample photo for ', panel)
                self.assertIn('Sample photo credits and licenses', panel)
                self.assertIn('Synthetic Seller ', panel)
                self.assertIn('data-demo-step="-1"', panel)
                self.assertIn('data-demo-step="1"', panel)
                self.assertEqual(self.source_panel(response, 'synthetic').count('data-demo-slide '), 4)
                self.assertIn('Synthetic dataset for demonstration only. Not actual customer purchases.', panel)
                for forbidden in ('Support', 'Confidence', 'Lift', 'transaction_count', 'rule_count',
                                  'View Dataset', 'View Recommendations', 'carousel-counter', '1/4', '1 of 4'):
                    self.assertNotIn(forbidden, panel)
                self.assertEqual(response.context['bundle_analysis']['source'], 'live')
                self.assertEqual(self.client.get(reverse('admin_dashboard_page')).status_code, 200)
                if label == 'super':
                    refresh = self.client.get(reverse('admin_dashboard_api'))
                    self.assertEqual(refresh.status_code, 200)
                    self.assertEqual(self.card(refresh.json()['bundle_preview_html']), panel)
                if directory:
                    target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                    (target / f'{label}.html').write_bytes(response.content)
                    if label == 'super':
                        (target / 'refresh.json').write_text(json.dumps(refresh.json()), encoding='utf-8')
        self.assertEqual(panels[0], panels[1])
        self.assertEqual(before, self.counts())
        self.assertEqual(dashboard_bundle_suggestions(self.root)['source'], 'live')

    def test_missing_stale_empty_and_corrupt_saved_reports_are_honest_and_never_auto_run(self):
        with patch('modules.marketplace.services.bundle_suggestions._analyze_synthetic_snapshot', side_effect=AssertionError):
            self.assertEqual(dashboard_synthetic_preview(self.root)['state'], 'not_generated')
        self.client.force_login(self.manager)
        missing = self.client.get(reverse('admin_dashboard_page'))
        self.assertIn('No saved demo bundles yet.', self.card(missing))
        self.export_state(missing, 'missing')
        execute_synthetic_research(self.root)
        with override_settings(CAMPUSHUB_BUNDLE_MIN_SUPPORT=.03):
            self.assertEqual(dashboard_synthetic_preview(self.root)['state'], 'not_generated')
        saved = json.loads(self.report.read_text())
        saved['rows'] = []
        self.report.write_text(json.dumps(saved))
        self.assertEqual(dashboard_synthetic_preview(self.root)['state'], 'empty')
        empty = self.client.get(reverse('admin_dashboard_page'))
        self.assertIn('No product pairs met the saved analysis criteria.', self.card(empty))
        self.export_state(empty, 'empty')
        self.report.write_text('{invalid')
        result = dashboard_synthetic_preview(self.manager)
        self.assertTrue(result['error'])
        self.assertEqual(result['rows'], [])
        self.client.force_login(self.manager)
        response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Refresh the dashboard to retry.', self.card(response))
        self.export_state(response, 'error')

    def export_state(self, response, name):
        directory = os.environ.get('DASHBOARD_DEMO_REVIEW_DIR')
        if directory:
            target = Path(directory); target.mkdir(parents=True, exist_ok=True)
            (target / f'{name}.html').write_bytes(response.content)

    def test_single_saved_pair_uses_fallbacks_without_unnecessary_navigation(self):
        execute_synthetic_research(self.root)
        saved = json.loads(self.report.read_text())
        saved['rows'] = saved['rows'][:1]
        saved['rows'][0]['products'][0]['name'] = 'Steamed Rice'
        saved['rows'][0]['products'][1]['name'] = 'Iced Tea'
        self.report.write_text(json.dumps(saved))
        data = dashboard_synthetic_preview(self.manager)
        self.assertEqual([p['fallback_kind'] for p in data['rows'][0]['products']], ['food', 'drink'])
        self.assertTrue(all(not p['image_url'] for p in data['rows'][0]['products']),
                        'Changed names must not accidentally inherit a different product photo.')
        self.client.force_login(self.manager)
        response = self.client.get(reverse('admin_dashboard_page'))
        panel = self.source_panel(response, 'synthetic')
        self.assertEqual(panel.count('data-demo-slide '), 1)
        self.assertNotIn('data-demo-controls', panel)
        self.assertNotIn('data-demo-go', panel)
        self.export_state(response, 'single')

    def test_permissions_restrict_demo_projection_and_raw_research_stays_super_only(self):
        facility = User.objects.create_user(username='demo-facility', role='Facilities Admin', is_staff=True)
        for actor in (facility, User.objects.create_user(username='demo-student', role='Student')):
            with self.assertRaises(PermissionDenied):
                dashboard_synthetic_preview(actor)
        permission = self.manager.user_permissions.get(codename='can_view_marketplace_analytics')
        self.manager.user_permissions.remove(permission)
        self.manager = User.objects.get(pk=self.manager.pk)
        with self.assertRaises(PermissionDenied):
            dashboard_synthetic_preview(self.manager)
        from modules.marketplace.services.bundle_suggestions import research_dataset, saved_synthetic_research, thresholds
        with self.assertRaises(PermissionDenied):
            saved_synthetic_research(self.manager, research_dataset(), thresholds())
        self.client.logout()
        self.assertEqual(self.client.get(reverse('admin_dashboard_api')).status_code, 401)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse('admin_dashboard_api')).status_code, 403)

    def test_template_escapes_saved_product_text_and_has_truthful_image_fallbacks(self):
        execute_synthetic_research(self.root)
        saved = json.loads(self.report.read_text())
        saved['rows'][0]['products'][0]['name'] = '<script>alert(1)</script>'
        self.report.write_text(json.dumps(saved))
        self.client.force_login(self.manager)
        panel = self.card(self.client.get(reverse('admin_dashboard_page')))
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', panel)
        self.assertNotIn('<script>alert', panel)
        self.assertIn('No image available for', panel)

    def test_demo_photo_assets_are_local_complete_and_do_not_change_live_photos(self):
        from django.contrib.staticfiles import finders
        from modules.marketplace.services.bundle_suggestions import SYNTHETIC_PREVIEW_PHOTOS
        for filename in SYNTHETIC_PREVIEW_PHOTOS.values():
            path = finders.find('marketplace/demo/bundles/' + filename)
            self.assertTrue(path, filename)
            self.assertTrue(Path(path).read_bytes().startswith(b'\xff\xd8'))
        credits = finders.find('marketplace/demo/bundles/credits.html')
        self.assertTrue(credits)
        text = Path(credits).read_text(encoding='utf-8')
        for filename in SYNTHETIC_PREVIEW_PHOTOS.values():
            self.assertIn(filename, text)
        self.a.image_url = '/media/actual-live-test-photo.jpg'
        self.a.save(update_fields=['image_url'])
        live = dashboard_bundle_suggestions(self.root)
        self.assertEqual(live['monitor_rows'][0]['products'][0]['image_url'], '/media/actual-live-test-photo.jpg')

    def test_live_empty_panel_matches_reference_without_products_or_actions_for_both_roles(self):
        execute_synthetic_research(self.root)
        self.row.delete()
        before = self.counts()
        for user in (self.root, self.manager):
            self.client.force_login(user)
            with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', side_effect=AssertionError('No mining')):
                response = self.client.get(reverse('admin_dashboard_page'))
            live = self.source_panel(response, 'live')
            self.assertIn('No Live Recommendations Yet', live)
            for forbidden in ('data-demo-slide', 'data-demo-controls', '<img', '<button', '<a ',
                              'Synthetic Seller', 'Seller Example', 'Details', 'Recommend to Seller', 'disclosure'):
                self.assertNotIn(forbidden, live)
            from django.utils.html import strip_tags
            self.assertEqual(' '.join(strip_tags(live).split()),
                             'No Live Recommendations Yet Recommendations will appear here once available.')
            self.assertIn('dashboard-bundle-demo__empty-title', live)
            self.assertIn('dashboard-bundle-demo__empty-hint', live)
            self.assertIn('Synthetic Seller S01', self.source_panel(response, 'synthetic'))
            self.export_state(response, 'live-empty-super' if user == self.root else 'live-empty-marketplace')
        self.assertEqual(before, self.counts())

    def test_real_saved_live_records_photos_seller_status_and_refresh_for_both_roles(self):
        from django.utils import timezone
        execute_synthetic_research(self.root)
        self.a.image_url = '/media/test-live-coffee.jpg'
        self.a.save(update_fields=['image_url'])
        self.b.image_url = '/media/test-live-cookie.jpg'
        self.b.save(update_fields=['image_url'])
        third = Product.objects.create(mobile_seller=self.seller, department=self.program,
            name='Actual saved third product', price=15, stock=10, approval_status='approved', image_url='/media/test-live-third.jpg')
        second = BundleRecommendation.objects.create(product_a=self.a, product_b=third, sent_at=timezone.now())
        before = self.counts()
        for label, user in [('super', self.root), ('marketplace', self.manager)]:
            self.client.force_login(user)
            with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', side_effect=AssertionError('No mining')):
                response = self.client.get(reverse('admin_dashboard_page'))
                panel = self.source_panel(response, 'live')
                self.assertEqual(panel.count('data-demo-slide '), 2)
                for text in ('Test Coffee', 'Test Cookie', 'Actual saved third product', 'Seller Example',
                             '/media/test-live-coffee.jpg', '/media/test-live-cookie.jpg',
                             'Not Sent to Seller', 'Awaiting Response', 'data-demo-controls'):
                    self.assertIn(text, panel)
                for forbidden in ('Synthetic Seller', 'Demo Only', 'Sample photo for', 'No Live Recommendations Yet',
                                  'Details', 'Recommend to Seller', 'Sample Seller', 'UI preview only'):
                    self.assertNotIn(forbidden, panel)
                if label == 'super':
                    refresh = self.client.get(reverse('admin_dashboard_api'))
                    self.assertEqual(self.source_panel(refresh.json()['bundle_preview_html'], 'live'), panel)
                    directory = os.environ.get('DASHBOARD_DEMO_REVIEW_DIR')
                    if directory:
                        (Path(directory) / 'live-refresh.json').write_text(json.dumps(refresh.json()), encoding='utf-8')
            self.export_state(response, 'live-records-' + label)
        self.assertEqual(before, self.counts())
        second.refresh_from_db()
        self.assertIsNotNone(second.sent_at)

    def test_live_status_is_recorded_seller_response_and_escapes_database_names(self):
        from django.utils import timezone
        from api.models import SellerBundleSuggestion
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=['sent_at'])
        SellerBundleSuggestion.objects.create(seller=self.seller, product_a=self.a, product_b=self.b, state='dismissed')
        self.a.name = '<script>database name</script>'
        self.a.save(update_fields=['name'])
        panel = self.source_panel(self.client.get(reverse('admin_dashboard_page')), 'live')
        self.assertIn('Dismissed', panel)
        self.assertIn('&lt;script&gt;database name&lt;/script&gt;', panel)
        self.assertNotIn('<script>database', panel)
        self.assertNotIn('Awaiting Response', panel)

    def test_live_scope_and_load_errors_do_not_expose_other_program_or_fake_empty(self):
        from django.db import DatabaseError
        from api.models import CampusHubUser, SellerRequest
        outsider = CampusHubUser.objects.create(username='tab-outsider', password_hash='unused', department=self.other)
        SellerRequest.objects.create(mobile_user=outsider, student_id='tab-outsider', full_name='Outside Seller', product_type='Products', status='approved')
        pair = [Product.objects.create(mobile_seller=outsider, department=self.other, name='Outside product '+str(i),
                                      price=10, stock=10, approval_status='approved') for i in range(2)]
        BundleRecommendation.objects.create(product_a=pair[0], product_b=pair[1])
        self.client.force_login(self.manager)
        panel = self.source_panel(self.client.get(reverse('admin_dashboard_page')), 'live')
        self.assertIn('Test Coffee', panel)
        self.assertNotIn('Outside product', panel)
        with patch('modules.marketplace.services.bundle_monitoring.recommendations_for', side_effect=DatabaseError('private')):
            panel = self.source_panel(self.client.get(reverse('admin_dashboard_page')), 'live')
        self.assertIn('Unable to load live recommendations.', panel)
        self.assertNotIn('No Live Recommendations Yet', panel)
        self.assertNotIn('private', panel)
