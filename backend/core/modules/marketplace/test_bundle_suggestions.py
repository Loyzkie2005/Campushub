"""Live recommendation boundaries and isolated research-only Apriori validation."""
import csv
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.db import DatabaseError
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse

from accounts.models import Department, User
from api.models import Booking, BundleRecommendation, Facility, MarketplaceOrder, Product, SellerRequest
from .services.analytics import calculate_market_basket
from .services.bundle_suggestions import (DATASET, DISCLOSURE, analyze_synthetic,
                                         analyze_live, build_bundle_suggestions, dashboard_bundle_suggestions,
                                         thresholds, _cached_synthetic, _recommendation_rows,
                                         recommendation_presentation)


class AprioriDemonstrationTests(SimpleTestCase):
    def mine(self, baskets, **kwargs):
        return calculate_market_basket([[(item, item) for item in basket] for basket in baskets],
            detailed=True, limit=None, minimum_support=.02, minimum_confidence=.30, minimum_lift=1, **kwargs)

    def test_support_confidence_and_lift_are_actual_basket_metrics(self):
        rows = self.mine([['A', 'B'], ['A', 'B'], ['A'], ['C']])['rows']
        rule = next(row for row in rows if row['product_a_id'] == 'A')
        self.assertEqual((rule['support'], rule['confidence'], rule['lift']), (50, 66.67, 1.33))
        self.assertEqual((rule['together_count'], rule['source_count'], rule['target_count']), (2, 3, 2))

    def test_non_positive_lift_is_excluded(self):
        self.assertEqual(self.mine([['A', 'B'], ['A', 'B'], ['A', 'B']])['rows'], [])

    def test_insufficient_and_single_product_baskets_are_empty(self):
        for baskets in ([['A', 'B']], [['A'], ['B'], ['C']]):
            self.assertFalse(self.mine(baskets)['sufficient'])

    def test_thresholds_filter_unrounded_values(self):
        baskets = [[('A', 'A'), ('B', 'B')]] * 2 + [[('A', 'A')], [('C', 'C')]]
        self.assertEqual(calculate_market_basket(baskets, minimum_support=.51, detailed=True)['rows'], [])
        rows = calculate_market_basket(baskets, minimum_confidence=.70, detailed=True)['rows']
        self.assertTrue(all(row['product_a_id'] == 'B' for row in rows))

    def test_existing_analytics_default_shape_is_preserved(self):
        result = calculate_market_basket([[('A', 'A'), ('B', 'B')]] * 3)
        self.assertEqual(set(result['rows'][0]), {'product_a', 'product_b', 'support', 'confidence', 'lift'})
        self.assertEqual(result['rows'][0]['lift'], 1)

    def test_equal_pair_deduplication_does_not_erase_cross_sell_direction(self):
        # Isolated algorithm fixture, never a live order or fallback dataset.
        baskets = [[(item, item) for item in basket] for basket in [('A', 'B'), ('A', 'B'), ('A',), ('C',)]]
        catalog = {key: {'id': key, 'name': key, 'seller_id': 1, 'seller': 'Test Seller', 'image_url': ''}
                   for key in ('A', 'B', 'C')}
        mined = calculate_market_basket(baskets, detailed=True, limit=None,
            minimum_support=.02, minimum_confidence=.30, minimum_lift=1)
        equal = _recommendation_rows(mined, catalog, source='live')
        directional = _recommendation_rows(mined, catalog, source='live', directional=True)
        self.assertEqual(len(equal), 1)
        self.assertEqual({row['id'] for row in directional}, {'A->B', 'B->A'})
        stricter = calculate_market_basket(baskets, detailed=True, limit=None,
            minimum_support=.02, minimum_confidence=.70, minimum_lift=1)
        qualified = _recommendation_rows(stricter, catalog, source='live', directional=True)
        self.assertEqual([row['id'] for row in qualified], ['B->A'])
        self.assertEqual([product['id'] for product in qualified[0]['products']], ['B', 'A'])
        catalog['B']['seller_id'] = 2
        self.assertEqual(_recommendation_rows(mined, catalog, source='live', directional=True), [])

    def test_presentation_has_independent_limits_and_retains_metrics_only_in_backend(self):
        baskets = [[(item, item) for item in basket] for basket in [('A', 'B'), ('A', 'B'), ('A',), ('C',)]]
        catalog = {key: {'id': key, 'name': key, 'seller_id': 1, 'seller': 'Test Seller', 'image_url': ''}
                   for key in ('A', 'B', 'C')}
        mined = calculate_market_basket(baskets, detailed=True, limit=None,
            minimum_support=.02, minimum_confidence=.30, minimum_lift=1)
        result = {'source': 'live', 'read_only': True, 'error': False, 'message': '', 'detail': '',
                  'transaction_count': 4, 'qualifying_pair_count': 1, 'page_size': 8, 'endpoint': '/test-only/',
                  'rows': _recommendation_rows(mined, catalog, source='live'),
                  'directional_rows': _recommendation_rows(mined, catalog, source='live', directional=True)}
        before = json.dumps(result)
        public = recommendation_presentation(result, limit=1)
        self.assertEqual(public['suggested_rows'], public['rows'][:1])
        self.assertFalse(public['suggested_has_more'])
        self.assertFalse(public['frequent_has_more'])
        self.assertTrue(public['cross_sell_has_more'])
        self.assertEqual((len(public['frequent_rows']), len(public['cross_sell_rows'])), (1, 1))
        for key in ('support', 'confidence', 'lift', 'thresholds'):
            self.assertNotIn(f'"{key}"', json.dumps(public))
        self.assertEqual(json.dumps(result), before)
        self.assertTrue(all({'support', 'confidence', 'lift'}.issubset(row) for row in result['directional_rows']))
        with self.assertRaises(ValueError):
            recommendation_presentation({**result, 'source': 'synthetic'})

    def test_actual_supplied_csv_is_separate_and_qualifies(self):
        result = analyze_synthetic(DATASET, (.02, .30, 1))
        self.assertEqual((result['transaction_count'], result['item_count'], result['multi_item_count']), (1000, 2027, 792))
        self.assertEqual((result['date_start'], result['date_end']), ('2026-07-01', '2026-09-28'))
        self.assertTrue(result['rows'])
        pairs = set()
        for row in result['rows']:
            pair = tuple(sorted((row['product_a_id'], row['product_b_id'])))
            self.assertNotIn(pair, pairs); pairs.add(pair)
            self.assertEqual(row['products'][0]['seller_id'], row['products'][1]['seller_id'])
            self.assertGreater(row['lift'], 1)
            self.assertEqual((row['source'], row['status'], row['read_only']), ('Synthetic', 'Generated', True))
            self.assertTrue(all(not product['image_url'] for product in row['products']))

    def csv(self, rows):
        root = TemporaryDirectory(); self.addCleanup(root.cleanup)
        path = Path(root.name) / 'test.csv'
        with path.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['transaction_id', 'date', 'seller_id', 'product_id', 'product_name', 'category', 'quantity', 'unit_price_php', 'data_origin'])
            writer.writeheader(); writer.writerows(rows)
        return path

    def row(self, **updates):
        return dict(transaction_id='T1', date='07/01/2026', seller_id='S1', product_id='P1',
            product_name='Product A', category='Snacks', quantity='1', unit_price_php='10', data_origin='SYNTHETIC', **updates)

    def test_cross_seller_transaction_is_rejected(self):
        left = self.row(); right = {**left, 'seller_id': 'S2', 'product_id': 'P2'}
        with self.assertRaisesRegex(ValueError, 'mix sellers'):
            analyze_synthetic(self.csv([left, right]), (.02, .30, 1))

    def test_unmarked_live_data_cannot_enter_synthetic_reader(self):
        row = {**self.row(), 'data_origin': 'LIVE'}
        with self.assertRaisesRegex(ValueError, 'explicitly synthetic'):
            analyze_synthetic(self.csv([row]), (.02, .30, 1))

    def test_duplicate_lines_and_quantities_do_not_inflate_basket(self):
        result = analyze_synthetic(self.csv([self.row(), {**self.row(), 'quantity': '3'}]), (.02, .30, 1))
        self.assertEqual((result['transaction_count'], result['multi_item_count']), (1, 0))

    def test_malformed_or_conflicting_catalog_rows_fail_honestly(self):
        for changes in ({'date': 'wrong'}, {'quantity': '0'}, {'unit_price_php': 'NaN'}, {'product_id': 'P:1'}):
            with self.assertRaises(ValueError):
                analyze_synthetic(self.csv([{**self.row(), **changes}]), (.02, .30, 1))
        with self.assertRaisesRegex(ValueError, 'conflicting catalog'):
            analyze_synthetic(self.csv([self.row(), {**self.row(), 'product_name': 'Changed'}]), (.02, .30, 1))

    @override_settings(CAMPUSHUB_BUNDLE_MIN_SUPPORT='.1', CAMPUSHUB_BUNDLE_MIN_CONFIDENCE='.5', CAMPUSHUB_BUNDLE_MIN_LIFT='2')
    def test_configured_thresholds_are_used(self):
        self.assertEqual(thresholds(), (.1, .5, 2))


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BundleSuggestionAccessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Dashboard reads legacy unmanaged tables even when the test dataset is empty.
        from django.db import connection
        from api.models import CampusHubUser, Facility, Room, Booking, FacilityPayment
        for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment):
            if model._meta.db_table not in connection.introspection.table_names():
                with connection.schema_editor() as editor:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.program = Department.objects.create(code='DSS', name='DSS', is_program=True)
        self.other = Department.objects.create(code='OTHER', name='Other', is_program=True)
        self.admin = User.objects.create_user(username='dss-admin', role='Marketplace Admin', is_staff=True, department=self.program)
        self.admin.user_permissions.add(*Permission.objects.filter(content_type__app_label='accounts', codename__in=['can_view_marketplace_analytics', 'can_view_orders']))
        self.seller = User.objects.create_user(username='dss-seller', role='User', department=self.program)
        SellerRequest.objects.create(user=self.seller, student_id='dss-seller', full_name='Actual Seller',
                                     product_type='Products', status=SellerRequest.STATUS_APPROVED)
        self.product = Product.objects.create(seller=self.seller, name='Live Product', price=20, stock=10, approval_status='approved', department=self.program)
        self.order = MarketplaceOrder.objects.create(product=self.product, product_name=self.product.name, quantity=1, total_price=20, status='completed', payment_status='paid')
        self.url = reverse('bundle_suggestions_api')
        self.client.force_login(self.admin)

    def test_api_get_is_readonly_and_does_not_affect_live_sales(self):
        before = (Product.objects.count(), MarketplaceOrder.objects.count(), self.product.stock)
        result = self.client.get(self.url).json()
        self.assertTrue(result['read_only']); self.assertEqual(result['rows'], [])
        self.assertEqual(result['source'], 'live')
        self.assertNotIn('disclosure', result)
        self.assertNotIn('thresholds', result)
        self.product.refresh_from_db()
        self.assertEqual((Product.objects.count(), MarketplaceOrder.objects.count(), self.product.stock), before)
        self.assertEqual(self.client.post(self.url, {'action': 'send'}).status_code, 405)

    def test_live_count_uses_completed_paid_records_and_scope(self):
        for status, payment in [('pending', 'paid'), ('cancelled', 'paid'), ('completed', 'unpaid')]:
            MarketplaceOrder.objects.create(product=self.product, product_name=self.product.name, total_price=100, status=status, payment_status=payment)
        outsider = Product.objects.create(seller=self.seller, name='Outside', price=10, stock=2, department=self.other)
        MarketplaceOrder.objects.create(product=outsider, product_name='Outside', total_price=10, status='completed', payment_status='paid')
        result = self.client.get(self.url, {'source': 'live'}).json()
        self.assertEqual(result['transaction_count'], 1); self.assertEqual(result['rows'], [])
        self.assertIn('No bundle suggestions available yet.', result['message'])
        self.assertNotIn('Outside', json.dumps(result)); self.assertNotIn('disclosure', result)

    def test_zero_live_orders_have_honest_empty_state(self):
        MarketplaceOrder.objects.all().delete()
        result = self.client.get(self.url, {'source': 'live'}).json()
        self.assertEqual(result['transaction_count'], 0); self.assertFalse(result['rows'])

    def test_missing_scope_fails_closed_for_live_counts(self):
        self.admin.department = None; self.admin.save(update_fields=['department'])
        self.assertEqual(self.client.get(self.url, {'source': 'live'}).json()['transaction_count'], 0)

    def test_permissions_normal_users_and_facilities_admin(self):
        self.client.logout(); self.assertEqual(self.client.get(self.url).status_code, 401)
        for user in (self.seller, User.objects.create_user(username='dss-facilities', role='Facilities Admin', is_staff=True)):
            self.client.force_login(user); self.assertEqual(self.client.get(self.url).status_code, 403)
        self.admin.user_permissions.clear(); self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_super_admin_retains_access(self):
        root = User.objects.create_superuser(username='dss-root', email='root@example.test', password='test')
        self.client.force_login(root); self.assertEqual(self.client.get(self.url).status_code, 200)

    @override_settings(CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH='missing-dss.csv')
    def test_failure_is_not_fabricated_zero_metrics(self):
        result = build_bundle_suggestions(self.admin, source='synthetic')
        self.assertTrue(result['error']); self.assertEqual(result['rows'], [])
        self.assertEqual(result['message'], 'Synthetic transaction dataset is unavailable.')

    def test_caching_never_creates_suggestions_on_refresh(self):
        _cached_synthetic.cache_clear()
        with patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', wraps=analyze_synthetic) as analyze:
            first = build_bundle_suggestions(self.admin, source='synthetic')
            second = build_bundle_suggestions(self.admin, source='synthetic')
        self.assertEqual(analyze.call_count, 1); self.assertEqual(first, second)
        first['rows'][0]['products'][0]['name'] = 'Mutation'
        self.assertNotEqual(build_bundle_suggestions(self.admin, source='synthetic')['rows'][0]['products'][0]['name'], 'Mutation')

    def test_marketplace_summary_reads_saved_records_without_mining(self):
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', wraps=build_bundle_suggestions) as mining:
            response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(mining.call_count, 0)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        anchors = ['id="marketplaceOverviewTitle"', 'id="dashboardAttentionTitle"', 'id="marketplaceRecommendationsTitle"',
                   'id="salesOverviewTitle"', 'id="marketplaceTopProductsTitle"', 'id="recentMarketplaceOrdersTitle"']
        self.assertEqual([html.index(anchor) for anchor in anchors], sorted(html.index(anchor) for anchor in anchors))
        self.assertNotContains(response, 'id="bundleReviewDialog"')
        self.assertNotContains(response, 'id="bundleAllDialog"')
        self.assertNotContains(response, 'bundle_suggestions.js')
        self.assertNotContains(response, 'id="frequentlyBoughtTogetherTitle"')
        self.assertNotContains(response, 'id="crossSellSuggestionsTitle"')
        self.assertNotContains(response, 'id="bundleLiftChart"')
        self.assertNotContains(response, 'id="bundleDataSource"')
        self.assertNotContains(response, 'Apriori Algorithm / Market Basket Analysis')
        analysis = response.context['bundle_analysis']
        self.assertEqual(analysis['dashboard_summary']['suggested'], 0)
        self.assertEqual(analysis['source'], 'live')
        for technical_label in ('>Support<', '>Confidence<', '>Lift<', 'bundle-pair-metrics', 'bundleReviewMetrics'):
            self.assertNotContains(response, technical_label)
        self.assertContains(response, 'No Bundle Suggestions Yet')
        self.assertNotContains(response, 'No Recommendation Activity Yet')
        self.assertContains(response, 'Suggested Product Bundles')
        self.assertNotIn('thresholds', analysis)
        self.assertNotContains(response, 'SYNTHETIC')
        self.assertNotContains(response, 'Synthetic Seller')
        self.assertNotContains(response, 'data-pair-id=')
        self.assertEqual(response.context['marketplace']['total_sales'], '20.00')
        self.assertEqual(response.context['marketplace']['total_orders'], 1)
        self.write_fixture(response, 'dashboard.html')

    def test_recommendation_scope_uses_seller_product_not_buyer_program(self):
        buyer = User.objects.create_user(username='outside-program-buyer', role='User', department=self.other)
        self.order.buyer_user_id = buyer.pk
        self.order.save(update_fields=['buyer_user_id'])
        with patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('No research fallback')):
            result = dashboard_bundle_suggestions(self.admin)
        self.assertEqual(result['dashboard_summary']['suggested'], 0)
        self.assertEqual(self.client.get(reverse('admin_dashboard_page')).context['marketplace']['total_sales'], '20.00')

    def write_fixture(self, response, name):
        destination = os.environ.get('BUNDLE_REVIEW_DIR')
        if destination:
            root = Path(destination); root.mkdir(parents=True, exist_ok=True)
            (root/name).write_bytes(response.content)
            (root/'live.json').write_text(json.dumps(self.client.get(self.url).json()), encoding='utf-8')
            if name == 'super-dashboard.html':
                (root/'global.json').write_text(json.dumps(self.client.get(reverse('admin_dashboard_api')).json()), encoding='utf-8')

    def test_super_admin_saved_results_and_kpi_area_suggestions(self):
        root = User.objects.create_superuser(username='dss-root-layout', email='layout@example.test', password='test')
        self.client.force_login(root)
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', wraps=build_bundle_suggestions) as mining:
            response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(mining.call_count, 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['bundle_analysis']['monitor_rows'], [])
        html = response.content.decode()
        anchors = ['id="marketplaceRecommendationsTitle"',
                   'id="facilitiesOverviewTitle"', 'id="servicesOverviewTitle"', 'id="recentActivitiesTitle"']
        self.assertEqual([html.index(anchor) for anchor in anchors], sorted(html.index(anchor) for anchor in anchors))
        self.assertNotContains(response, 'Marketplace Decision Support')
        self.assertNotContains(response, 'marketplaceDecisionSupportTitle')
        self.assertNotContains(response, 'id="crossSellSuggestions"')
        self.assertNotContains(response, 'id="frequentlyBoughtTogether"')
        self.assertNotContains(response, 'id="bundleSuggestions"')
        self.assertNotContains(response, 'id="recommendationActivity"')
        self.assertNotContains(response, 'class="marketplace-recommendation-counts"')
        self.assertNotContains(response, 'id="bundleReviewDialog"')
        self.assertContains(response, 'dashboard-summary-aside', count=1)
        self.assertContains(response, 'id="marketplaceRecommendationsTitle"', count=1)
        self.assertContains(response, 'Suggested Product Bundles')
        self.assertNotContains(response, 'id="bundleSuggestionsTitle"')
        self.assertNotContains(response, 'id="recommendationActivityTitle"')
        self.assertNotContains(response, 'id="categorySalesCard"')
        self.assertContains(response, 'id="topSellingProductsCard"', count=1)
        for technical_label in ('>Support<', '>Confidence<', '>Lift<', 'bundle-pair-metrics', 'bundleReviewMetrics'):
            self.assertNotContains(response, technical_label)
        self.assertEqual(response.context['bundle_analysis']['dashboard_limit'], 2)
        self.assertNotContains(response, 'id="bundleLiftChart"')
        self.assertEqual(self.client.get(self.url).json()['source'], 'live')
        self.assertNotContains(response, 'SYNTHETIC')
        self.assertNotContains(response, 'Synthetic Seller')
        self.assertNotContains(response, 'Frequently Bought Together')
        self.assertNotContains(response, 'Cross-Selling Opportunities')
        self.assertNotContains(response, 'No Recommendation Activity Yet')
        self.assertContains(response, reverse('bundle_monitor_list'))
        self.assertNotContains(response, reverse('bundle_monitor_activity'))
        self.assertEqual(self.client.get(reverse('bundle_monitor_activity')).status_code, 200)
        self.assertContains(response, 'Suggested Product Bundles', count=1)
        self.assertContains(response, 'No Bundle Suggestions Yet')
        self.assertEqual(response.context['bundle_analysis']['dashboard_summary']['suggested'], 0)
        self.assertNotContains(response, 'data-pair-id=')
        self.write_fixture(response, 'super-dashboard.html')

    def test_analytics_recommendation_table_has_no_csv_dependency_or_metric_columns(self):
        with patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('CSV read')):
            response = self.client.get(reverse('admin_marketplace_analytics_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Frequently Bought Together')
        for text in ('>Support<', '>Confidence<', '>Lift<', 'SYNTHETIC', 'Synthetic Seller'):
            self.assertNotContains(response, text)

    def test_super_dashboard_activity_uses_real_links_and_independent_error_state(self):
        from types import SimpleNamespace
        from django.utils import timezone
        from api.models import BundleRecommendation
        from .services.bundle_monitoring import record_event, link_created_bundle
        second = Product.objects.create(seller=self.seller, name='Activity paired product', price=10,
            stock=10, approval_status='approved', department=self.program)
        row = BundleRecommendation.objects.create(product_a=self.product, product_b=second,
            sent_at=timezone.now(), sent_by=self.admin)
        bundle = Product.objects.create(seller=self.seller, name='Seller-created test bundle', price=25,
            product_type='bundle', department=self.program)
        actor = SimpleNamespace(user=self.admin, META={})
        record_event(actor, row, 'BUNDLE_SUGGESTION_HIGHLIGHTED', 'Suggestion highlighted in seller workspace.')
        link_created_bundle(actor, bundle, [self.product.pk, second.pk])
        root = User.objects.create_superuser(username='activity-dashboard-root', email='activity@example.test', password='test')
        self.client.force_login(root)
        response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['bundle_analysis']['activity']['summary'],
            {'sent': 1, 'awaiting': 0, 'created': 1, 'dismissed': 0})
        self.assertNotContains(response, 'No Recommendation Activity Yet')
        self.assertEqual(response.context['bundle_analysis']['dashboard_summary'], {'suggested': 1, 'sent': 1, 'awaiting': 0, 'created': 1})
        self.write_fixture(response, 'activity-super-dashboard.html')
        self.write_fixture(self.client.get(reverse('bundle_monitor_activity')), 'recorded-activity.html')
        self.write_fixture(self.client.get(reverse('bundle_monitor_detail', args=[row.pk])), 'recorded-details.html')
        with patch('modules.marketplace.services.bundle_monitoring.activity_summary', side_effect=DatabaseError):
            failed = self.client.get(reverse('admin_dashboard_page'))
        self.assertTrue(failed.context['bundle_analysis']['activity']['error'])
        self.assertIsNone(failed.context['bundle_analysis']['activity']['summary'])
        self.assertNotContains(failed, 'Unable to load recommendation activity')
        self.assertContains(failed, 'Activity paired product')
        self.assertNotContains(failed, 'No Recommendation Activity Yet')

    @override_settings(CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH='missing-dss.csv')
    def test_missing_csv_does_not_affect_normal_dashboard(self):
        with patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('CSV read')):
            response = self.client.get(reverse('admin_dashboard_page'))
        self.assertFalse(response.context['bundle_analysis']['error'])
        self.assertEqual(response.context['bundle_analysis']['dashboard_summary']['suggested'], 0)
        self.assertEqual(response.context['marketplace']['total_sales'], '20.00')
        self.assertNotContains(response, 'data-pair-id=')
        self.assertNotIn('frequent_has_more', response.context['bundle_analysis'])

    def test_live_analysis_failure_has_retry_without_csv_fallback(self):
        with patch('modules.marketplace.services.bundle_monitoring.recommendations_for', side_effect=DatabaseError('Unavailable')), \
             patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('CSV fallback')):
            response = self.client.get(reverse('admin_dashboard_page'))
        self.assertTrue(response.context['bundle_analysis']['error'])
        self.assertNotIn('transaction_count', response.context['bundle_analysis'])
        self.assertContains(response, 'Unable to load bundle suggestions.')
        self.assertIsNone(response.context['bundle_analysis']['dashboard_summary']['suggested'])
        self.assertNotContains(response, 'data-pair-id=')
        self.write_fixture(response, 'error-dashboard.html')

    @override_settings(CAMPUSHUB_BUNDLE_MIN_SUPPORT='1')
    def test_no_saved_rules_shows_compact_zero_summary(self):
        response = self.client.get(reverse('admin_dashboard_page'))
        self.assertContains(response, 'No Bundle Suggestions Yet')
        self.assertNotContains(response, 'No Recommendation Activity Yet')
        self.assertNotIn('frequent_has_more', response.context['bundle_analysis'])
        self.assertNotContains(response, 'data-pair-id=')
        self.write_fixture(response, 'empty-dashboard.html')

    def test_no_analytics_permission_hides_both_panels_and_payload(self):
        self.admin.user_permissions.remove(Permission.objects.get(content_type__app_label='accounts', codename='can_view_marketplace_analytics'))
        response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(response.status_code, 200)
        for marker in ('bundleSuggestions', 'frequentlyBoughtTogether', 'crossSellSuggestions', 'bundle_suggestions.js'):
            self.assertNotContains(response, marker)
        self.assertIsNone(response.context['bundle_analysis'])

    @override_settings(CAMPUSHUB_BUNDLE_MIN_SUPPORT='.001', CAMPUSHUB_BUNDLE_MIN_CONFIDENCE='.01')
    def test_research_still_uses_additional_actual_csv_rules_only_when_explicit(self):
        analysis = build_bundle_suggestions(self.admin, source='synthetic')
        self.assertGreater(len(analysis['rows']), analysis['page_size'])
        self.assertTrue(all({'support', 'confidence', 'lift'}.issubset(row) for row in analysis['rows']))
        self.assertEqual(self.client.get(self.url).json()['rows'], [])

    def test_live_endpoint_rejects_synthetic_and_unknown_sources(self):
        with patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('CSV read')):
            for source in ('synthetic', '', 'unknown'):
                self.assertEqual(self.client.get(self.url, {'source': source}).status_code, 400)

    def test_live_calculator_receives_real_products_and_configured_thresholds(self):
        self.product.name = 'Current Product Name'
        self.product.save(update_fields=['name'])
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', wraps=calculate_market_basket) as mine, \
             patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('CSV read')):
            result = build_bundle_suggestions(self.admin)
        self.assertEqual(mine.call_args.args[0], [[(str(self.product.pk), 'Current Product Name')]])
        self.assertEqual(mine.call_args.kwargs, {'minimum_support': .02, 'minimum_confidence': .30,
                                               'minimum_lift': 1, 'detailed': True, 'limit': None})
        self.assertEqual((result['transaction_count'], result['multi_item_count'], result['rows']), (1, 0, []))

    def test_single_item_orders_quantities_and_bundle_recipes_never_invent_pairs(self):
        second = Product.objects.create(seller=self.seller, name='Second Product', price=10, stock=5,
                                        approval_status='approved', department=self.program)
        bundle = Product.objects.create(seller=self.seller, name='Existing Meal', price=20, product_type='bundle',
                                        approval_status='approved', department=self.program)
        for product, quantity, customization in (
                (second, 20, {}), (self.product, 10, {}),
                (bundle, 1, {'bundle_components': [{'product_id': self.product.pk}, {'product_id': second.pk}]})):
            MarketplaceOrder.objects.create(product=product, product_name=product.name, buyer_user_id=999,
                quantity=quantity, total_price=20, status='completed', payment_status='paid', customization=customization)
        MarketplaceOrder.objects.filter(pk=self.order.pk).update(order_code=None)
        result = build_bundle_suggestions(self.admin)
        self.assertEqual((result['transaction_count'], result['multi_item_count'], result['rows']), (4, 0, []))

    def test_live_catalog_uses_saved_product_photo_and_actual_seller(self):
        self.seller.first_name, self.seller.last_name = 'Actual', 'Seller'
        self.seller.save(update_fields=['first_name', 'last_name'])
        self.product.image_url = '["/media/products/real-product.png", "/media/products/second.png"]'
        self.product.save(update_fields=['image_url'])
        with patch('modules.marketplace.services.bundle_suggestions._recommendation_rows', wraps=_recommendation_rows) as formatter:
            analyze_live(self.admin, thresholds())
        catalog = formatter.call_args.args[1]
        self.assertEqual(catalog[str(self.product.pk)], {
            'id': self.product.pk, 'seller_id': self.seller.pk, 'seller': 'Actual Seller',
            'name': self.product.name, 'category': self.product.category, 'price': '20.00',
            'image_url': '/media/products/real-product.png'})
        self.assertEqual(formatter.call_args_list[0].kwargs, {'source': 'live'})
        self.assertEqual(formatter.call_args_list[1].kwargs, {'source': 'live', 'directional': True})

    def test_directional_targets_use_existing_inventory_without_removing_historical_pairs(self):
        second = Product.objects.create(seller=self.seller, name='Test Second', price=10, stock=0,
                                        approval_status='approved', department=self.program)
        MarketplaceOrder.objects.create(product=second, product_name=second.name, quantity=1,
            status='completed', payment_status='paid', total_price=10)
        left, right = (str(self.product.pk), self.product.name), (str(second.pk), second.name)
        # Mock only the missing multi-item capture boundary, using genuinely
        # calculated test baskets and actual test DB catalog/stock records.
        mined = calculate_market_basket([[left, right], [left, right], [left], [('test-other', 'Other')]],
            detailed=True, limit=None, minimum_support=.02, minimum_confidence=.30, minimum_lift=1)
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', return_value=mined):
            result = analyze_live(self.admin, thresholds())
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual([row['product_b_id'] for row in result['directional_rows']], [str(self.product.pk)])

    def test_populated_cards_render_only_actual_test_catalog_from_isolated_mined_fixture(self):
        products = [self.product]
        for number in range(1, 10):
            product = Product.objects.create(seller=self.seller, name=f'Test Product {number}',
                price=10, stock=5, approval_status='approved', department=self.program)
            MarketplaceOrder.objects.create(product=product, product_name=product.name,
                total_price=10, status='completed', payment_status='paid')
            products.append(product)
        baskets = []
        for offset in range(0, 10, 2):
            basket = [(str(product.pk), product.name) for product in products[offset:offset + 2]]
            baskets.extend([basket, basket])
        # Test-only multi-item fixture exercises the populated renderer. It does
        # not claim today's single-product checkout stores these basket groups.
        mined = calculate_market_basket(baskets, detailed=True, limit=None,
            minimum_support=.02, minimum_confidence=.30, minimum_lift=1)
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', return_value=mined):
            root = User.objects.create_superuser(username='saved-fixture-root', email='saved@example.test', password='test')
            from .services.bundle_monitoring import refresh_live
            evidence = build_bundle_suggestions(root)
            evidence['_analysis_basket_scopes'] = [{'program_id': self.program.pk, 'major_id': None,
                'baskets': len(baskets), 'multi_item_baskets': len(baskets)}]
            with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=evidence):
                refresh_live(root)
            response = self.client.get(reverse('admin_dashboard_page'))
            self.assertEqual(response.status_code, 200)
            analysis = response.context['bundle_analysis']
            self.assertEqual(analysis['dashboard_summary']['suggested'], 5)
            self.assertNotContains(response, 'Recommended with')
            self.assertNotContains(response, 'bundle-pair--cross-sell')
            self.assertNotContains(response, 'data-bundle-review=')
            self.assertContains(response, 'Suggested Product Bundles')
            self.assertEqual(analysis['dashboard_summary']['suggested'], 5)
            for key in ('support', 'confidence', 'lift', 'thresholds'):
                self.assertNotIn(f'"{key}"', json.dumps(analysis))
            api = self.client.get(self.url).json()
            self.assertEqual(len(api['directional_rows']), 10)
            admin = User.objects.create_superuser(username='pairs-test-root', email='pairs@example.test', password='test')
            self.client.force_login(admin)
            from .services.bundle_monitoring import refresh_live
            # Persist the same explicitly supplied multi-item test evidence.
            with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=evidence):
                refresh_live(admin)
            super_response = self.client.get(reverse('admin_dashboard_page'))
            self.assertContains(super_response, 'id="marketplaceRecommendationsTitle"', count=1)
            self.assertNotContains(super_response, 'id="frequentlyBoughtTogether"')
            self.assertNotContains(super_response, 'id="crossSellSuggestions"')
            self.assertNotContains(super_response, 'id="recommendationActivity"')
            self.assertContains(super_response, 'data-recommendation-id=', count=2)
            self.assertEqual(super_response.context['bundle_analysis']['dashboard_summary']['suggested'], 5)
            self.assertEqual(len(super_response.context['bundle_analysis']['monitor_rows']), 2)
            self.assertNotIn('frequent_rows', super_response.context['bundle_analysis'])
            destination = os.environ.get('BUNDLE_REVIEW_DIR')
            if destination:
                root = Path(destination); root.mkdir(parents=True, exist_ok=True)
                (root/'populated-dashboard.html').write_bytes(response.content)
                (root/'populated.json').write_text(json.dumps(api), encoding='utf-8')
                (root/'populated-super-dashboard.html').write_bytes(super_response.content)

    def test_unverified_legacy_item_snapshots_are_not_order_items(self):
        self.order.customization = {'items': [{'product_id': self.product.pk}, {'product_name': 'Unverified'}]}
        self.order.save(update_fields=['customization'])
        root = User.objects.create_superuser(username='legacy-root', email='legacy@example.test', password='test')
        self.assertEqual(build_bundle_suggestions(root)['transaction_count'], 0)

    def test_unapproved_archived_missing_products_and_suspended_sellers_are_excluded(self):
        for field, value in (('approval_status', 'pending'), ('is_archived', True)):
            original = getattr(self.product, field)
            setattr(self.product, field, value)
            self.product.save(update_fields=[field])
            self.assertEqual(build_bundle_suggestions(self.admin)['transaction_count'], 0)
            setattr(self.product, field, original)
            self.product.save(update_fields=[field])
        self.seller.is_suspended = True
        self.seller.save(update_fields=['is_suspended'])
        self.assertEqual(build_bundle_suggestions(self.admin)['transaction_count'], 0)
        self.seller.is_suspended = False
        self.seller.save(update_fields=['is_suspended'])
        self.order.product = None
        self.order.save(update_fields=['product'])
        self.assertEqual(build_bundle_suggestions(self.admin)['transaction_count'], 0)

    def test_live_analysis_uses_bounded_queries_and_does_not_read_csv(self):
        self.admin.has_perm('accounts.can_view_orders')  # Warm Django's permission cache.
        with self.assertNumQueries(2), \
             patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('CSV read')):
            self.assertEqual(analyze_live(self.admin, thresholds())['transaction_count'], 1)

    def test_analysis_metadata_counts_only_the_baskets_actually_processed(self):
        for status, payment in [('completed','unpaid'),('pending','paid'),('cancelled','paid')]:
            MarketplaceOrder.objects.create(product=self.product, product_name=self.product.name,
                quantity=2,total_price=40,status=status,payment_status=payment)
        MarketplaceOrder.objects.create(product=self.product, product_name=self.product.name, quantity=1,
            total_price=20,status='completed',payment_status='paid',customization={'items':[{'product_id':self.product.pk}]})
        result = analyze_live(self.admin, thresholds())
        self.assertEqual(result['transaction_count'], 1)
        self.assertEqual(result['_analysis_basket_scopes'], [{'program_id':self.program.pk,'major_id':None,
            'baskets':1,'multi_item_baskets':0}])
        response = self.client.get(self.url).json()
        self.assertNotIn('_analysis_basket_scopes', response)

    def test_domain_overviews_use_existing_service_and_account_records(self):
        root = User.objects.create_superuser(username='dss-domain-root', email='domain@example.test', password='test')
        self.seller.is_suspended = True; self.seller.save(update_fields=['is_suspended'])
        service = Facility.objects.create(id='DSS-LAB', facility_name='Test configured lab', facility_type='food_analysis', booking_mode='service')
        Facility.objects.create(id='DSS-COURT', facility_name='Test physical court', facility_type='covered_court', booking_mode='slot')
        Facility.objects.create(id='DSS-ARCHIVED-LAB', facility_name='Archived lab', facility_type='food_analysis', booking_mode='service', is_archived=True)
        Booking.objects.create(id='DSS-LAB-PENDING', facility=service, status=Booking.STATUS_PENDING)
        self.client.force_login(root)
        response = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['services_overview'], {'total': 1, 'open': 1, 'pending': 1})
        self.assertEqual(response.context['accounts_overview'], {'total': 3, 'enabled': 2, 'restricted': 1})
        refreshed = self.client.get(reverse('admin_dashboard_api')).json()
        self.assertEqual(refreshed['services_overview'], response.context['services_overview'])
        self.assertEqual(refreshed['accounts_overview'], response.context['accounts_overview'])
