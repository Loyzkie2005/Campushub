# Original location: backend/core/api/test_seller_recommendations.py
"""Actual CSV calculation, seller-safe projection, ownership and action checks."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.test import override_settings
from django.urls import reverse

from api.tests import test_mobile_seller_workspace as fixtures
from api.models import Product, MarketplaceOrder, SellerBundleSuggestion
from accounts.models import AccountActivity
from modules.marketplace.services.bundle_suggestions import (
    DATASET, execute_synthetic_research, research_dataset, saved_synthetic_research, thresholds)


class SellerRecommendationTests(fixtures.MobileSellerWorkspaceTests):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.demo_path = Path(directory.name) / 'seller-demo.json'
        report_settings = override_settings(CAMPUSHUB_SELLER_DEMO_REPORT_PATH=str(self.demo_path))
        report_settings.enable()
        self.addCleanup(report_settings.disable)
        cache.clear()
        super().setUp()
        self.root = get_user_model().objects.create_superuser(
            username='demo-research-root', password='test-only-password', role='Super Admin')

    def demo(self):
        return execute_synthetic_research(self.root)

    def recommendations(self, source='live', **auth):
        return self.client.get(reverse('mobile_seller_recommendations'), {'source': source}, **(auth or self.auth))

    def action(self, row, action='validate', **extra):
        return self.client.post(reverse('mobile_seller_recommendation_action'), json.dumps({
            'id': row['id'], 'source': row.get('source', 'live'),
            'revision': row.get('revision', ''), 'action': action, **extra}),
            content_type='application/json', **self.auth)

    def mapping(self, saved):
        row = saved['result']['rows'][0]
        return {f"{item['seller_id']}:{item['id']}": product.pk
                for item, product in zip(row['products'], (self.own, self.second))}

    def test_demo_requires_prior_authorized_analysis_and_never_mines_on_get(self):
        with self.assertRaises(PermissionDenied):
            from django.contrib.auth.models import AnonymousUser
            execute_synthetic_research(AnonymousUser())
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', side_effect=AssertionError('GET cannot mine')):
            result = self.recommendations('synthetic').json()
        self.assertEqual(result['rows'], [])
        self.assertFalse(result['available'])
        self.assertFalse(result['error'])
        self.assertEqual(result['status'], 'not_generated')
        saved = self.demo()
        self.assertGreater(len(saved['result']['rows']), 0)
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', side_effect=AssertionError('GET cannot mine')):
            result = self.recommendations('synthetic').json()
        self.assertEqual(len(result['rows']), len(saved['result']['rows']))
        self.assertEqual(result['status'], 'ready')
        self.assertIn('does not represent actual', result['disclosure'])
        for forbidden in ('support', 'confidence', 'lift', 'thresholds', 'transaction_count'):
            self.assertNotIn(forbidden, json.dumps(result).lower())
        self.assertEqual(saved_synthetic_research(self.root, research_dataset(), thresholds()), saved)
        self.assertIn('support', saved['result']['rows'][0])

    def test_completed_demo_survives_cache_clear_and_an_independent_process(self):
        import os
        import subprocess
        import sys
        saved = self.demo()
        report = json.loads(self.demo_path.read_text(encoding='utf-8'))
        self.assertNotIn('support', json.dumps(report))
        cache.clear()
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket',
                   side_effect=AssertionError('Seller GET cannot mine')):
            response = self.recommendations('synthetic').json()
        self.assertEqual(len(response['rows']), len(saved['result']['rows']))
        self.assertTrue(all(row['synthetic_seller_id'] for row in response['rows']))
        script = '''import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()
from django.conf import settings
settings.CAMPUSHUB_SELLER_DEMO_REPORT_PATH = os.environ['TEST_DEMO_REPORT']
from modules.marketplace.services.seller_recommendations import _demo
assert len(_demo()['rows']) == 4
'''
        process = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[2],
            env={**os.environ, 'TEST_DEMO_REPORT': str(self.demo_path)},
            capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_demo_states_distinguish_no_pairs_corrupt_report_and_changed_dataset(self):
        with override_settings(CAMPUSHUB_BUNDLE_MIN_LIFT=100):
            self.demo()
            result = self.recommendations('synthetic').json()
            self.assertEqual(result['status'], 'no_qualifying_pairs')
            self.assertEqual(result['rows'], [])
        self.demo_path.write_text('{broken', encoding='utf-8')
        self.assertEqual(self.recommendations('synthetic').json()['status'], 'error')
        self.demo()
        with override_settings(CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH=str(self.demo_path)):
            self.assertEqual(self.recommendations('synthetic').json()['status'], 'not_generated')

    def test_report_publish_failure_preserves_previous_completed_report(self):
        self.demo()
        original = self.demo_path.read_bytes()
        with patch('modules.marketplace.services.seller_recommendations.os.replace',
                   side_effect=OSError('test-only write failure')):
            with self.assertRaises(OSError):
                self.demo()
        self.assertEqual(self.demo_path.read_bytes(), original)
        self.assertEqual(list(self.demo_path.parent.glob('.seller-demo-*.tmp')), [])

    def test_unmapped_demo_has_no_real_images_or_creatable_products(self):
        self.demo()
        result = self.recommendations('synthetic').json()
        row = result['rows'][0]
        self.assertFalse(row['can_create'])
        self.assertTrue(row['creation_reason'])
        self.assertTrue(all(product['catalog_id'] is None and not product['image_url'] for product in row['products']))
        self.assertEqual(self.action(row).status_code, 409)

    def test_explicit_mapping_is_rechecked_against_owner_and_database(self):
        saved = self.demo()
        mapping = self.mapping(saved)
        self.own.image_url = '/media/products/verified.png'
        self.own.save(update_fields=['image_url'])
        with override_settings(CAMPUSHUB_SYNTHETIC_PRODUCT_MAP=mapping):
            row = self.recommendations('synthetic').json()['rows'][0]
            self.assertTrue(row['can_create'])
            response = self.action(row)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(self.action(row, revision='stale').status_code, 409)
            self.assertEqual({p['id'] for p in response.json()['products']}, {self.own.pk, self.second.pk})
            self.assertIn('/media/products/verified.png', [p['image_url'] for p in row['products']])
            self.own.is_archived = True
            self.own.save(update_fields=['is_archived'])
            self.assertEqual(self.action(row).status_code, 409)
        mapping[next(iter(mapping))] = self.foreign.pk
        with override_settings(CAMPUSHUB_SYNTHETIC_PRODUCT_MAP=mapping):
            row = self.recommendations('synthetic').json()['rows'][0]
            self.assertFalse(row['can_create'])
            self.assertNotIn(self.foreign.name, json.dumps(row))
            self.assertEqual(self.action(row).status_code, 409)

    def test_demo_submit_cannot_create_marketplace_records_even_with_verified_mapping(self):
        saved = self.demo()
        from api.models import BundleRecommendation, BundleComponent
        BundleRecommendation.objects.create(product_a=self.own, product_b=self.second)
        before = (Product.objects.count(), BundleComponent.objects.count(), MarketplaceOrder.objects.count(),
                  AccountActivity.objects.count(), self.own.stock, self.second.stock)
        with override_settings(CAMPUSHUB_SYNTHETIC_PRODUCT_MAP=self.mapping(saved)):
            row = self.recommendations('synthetic').json()['rows'][0]
            data = self.bundle_payload()
            data.update(suggestion_source='synthetic', suggestion_id=row['id'], suggestion_revision=row['revision'])
            response = self.submit_bundle(data)
            self.assertEqual(response.status_code, 400, response.content)
            self.assertIn('device-local', response.json()['error'])
        self.own.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual(before, (Product.objects.count(), BundleComponent.objects.count(), MarketplaceOrder.objects.count(),
                                 AccountActivity.objects.count(), self.own.stock, self.second.stock))
        self.assertFalse(AccountActivity.objects.filter(activity_type='BUNDLE_CREATED_FROM_DEMO').exists())

    def test_dismiss_is_persistent_scoped_idempotent_and_preserves_saved_state(self):
        pair = f'{self.own.pk}|{self.second.pk}'
        choice = SellerBundleSuggestion.objects.create(seller=self.owner, product_a=self.own,
            product_b=self.second, state='saved')
        with patch('modules.marketplace.mobile_seller_views.live_suggestions', return_value=self.fake_qualified_result()):
            row = self.recommendations().json()['rows'][0]
            self.assertEqual(self.action(row, 'dismiss').status_code, 200)
            self.assertEqual(self.action(row, 'dismiss').status_code, 200)
            self.assertEqual(self.recommendations().json()['rows'], [])
            self.assertEqual(self.get()['recommendations']['rows'], [])
            self.assertEqual(len(self.get()['saved_suggestions']), 1)
            self.assertEqual(self.action(row).status_code, 409)
        choice.refresh_from_db()
        self.assertEqual(choice.state, 'saved')
        self.assertEqual(AccountActivity.objects.filter(activity_type='SELLER_RECOMMENDATION_DISMISSED').count(), 1)
        self.assertEqual(choice.product_a_id, self.own.pk)

    def test_demo_dismiss_does_not_change_csv_orders_sales_stock_or_other_rows(self):
        before = hashlib.sha256(DATASET.read_bytes()).hexdigest()
        self.demo()
        rows = self.recommendations('synthetic').json()['rows']
        orders, stock = MarketplaceOrder.objects.count(), self.own.stock
        self.assertEqual(self.action(rows[0], 'dismiss').status_code, 200)
        after = self.recommendations('synthetic').json()['rows']
        self.assertEqual([row['id'] for row in after], [row['id'] for row in rows[1:]])
        self.assertEqual(MarketplaceOrder.objects.count(), orders)
        self.own.refresh_from_db()
        self.assertEqual(self.own.stock, stock)
        self.assertEqual(hashlib.sha256(DATASET.read_bytes()).hexdigest(), before)
        with override_settings(CAMPUSHUB_BUNDLE_MIN_LIFT=100):
            self.assertFalse(self.recommendations('synthetic').json()['available'])

    def test_live_validation_rejects_foreign_stale_and_forged_demo_ids(self):
        with patch('modules.marketplace.mobile_seller_views.live_suggestions', return_value=self.fake_qualified_result()):
            row = self.recommendations().json()['rows'][0]
            self.assertEqual(self.action(row).status_code, 200)
            self.assertEqual(self.action(row, source='synthetic').status_code, 409)
            self.assertEqual(self.action(row, id=f'{self.own.pk}|{self.foreign.pk}').status_code, 409)
            self.application.is_suspended = True
            self.application.save()
            self.assertEqual(self.action(row).status_code, 403)
            self.assertEqual(self.recommendations().status_code, 403)

    def test_new_endpoints_require_approved_authentication_and_sources_are_separate(self):
        self.assertEqual(self.client.get(reverse('mobile_seller_recommendations')).status_code, 401)
        self.assertEqual(self.recommendations('forged').status_code, 400)
        self.demo()
        demo_rows = self.recommendations('synthetic').json()['rows']
        self.assertTrue(demo_rows)
        self.assertEqual(self.recommendations('live').json()['rows'], [])
        self.assertTrue(all(row['source'] == 'synthetic' for row in demo_rows))
