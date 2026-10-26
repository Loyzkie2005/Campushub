"""Isolated monitoring tests; no fixtures are loaded into the development database."""
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, DatabaseError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AccountActivity, Department, ProgramMajor, User
from api.models import BundleComponent, BundleRecommendation, CampusHubUser, Product, SellerBundleSuggestion, SellerRequest
from .services.analytics import calculate_market_basket
from .services.bundle_suggestions import _recommendation_rows, dashboard_bundle_suggestions
from .services.bundle_monitoring import (highlight, link_created_bundle, refresh_live,
    activity_summary, activity_events_for, record_event)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BundleMonitoringTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Super Admin navigation tests read these existing unmanaged models too.
        # Prepare them only in Django's disposable test database, outside class atomics.
        from api.models import Room, Booking, FacilityPayment, FacilityFeedback
        tables = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Room, Booking, FacilityPayment, FacilityFeedback):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
                    tables.add(model._meta.db_table)
        super().setUpClass()

    def setUp(self):
        self.program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name": "Information Technology", "is_program": True})
        self.other, _ = Department.objects.get_or_create(code="BFPT", defaults={"name": "Food Technology", "is_program": True})
        self.root = User.objects.create_superuser(username="monitor-root", password="test", email="root@example.test")
        self.manager = User.objects.create_user(username="monitor-manager", role="Marketplace Admin", is_staff=True, department=self.program)
        self.manager.user_permissions.add(*Permission.objects.filter(content_type__app_label="accounts",
            codename__in=["can_view_marketplace_analytics", "can_view_orders", "can_manage_sellers"]))
        self.seller = CampusHubUser.objects.create(first_name="Seller", last_name="Example", username="monitor-seller",
            email="seller@example.test", password_hash="unused", department=self.program)
        SellerRequest.objects.create(mobile_user=self.seller, student_id="monitor-seller", full_name="Seller Example",
            product_type="Products", status="approved")
        self.a = Product.objects.create(mobile_seller=self.seller, department=self.program,
            name="Test Coffee", category="Beverages", price=30, stock=20, approval_status="approved")
        self.b = Product.objects.create(mobile_seller=self.seller, department=self.program,
            name="Test Cookie", category="Food", price=10, stock=20, approval_status="approved")
        self.row = BundleRecommendation.objects.create(product_a=self.a, product_b=self.b, metrics={"support": 25, "confidence": 80, "lift": 2})
        self.client.force_login(self.root)

    def test_source_tabs_dataset_never_mines_or_reads_live_recommendations(self):
        from .services.bundle_suggestions import _cached_synthetic
        before = (BundleRecommendation.objects.count(), AccountActivity.objects.count())
        cache_before = _cached_synthetic.cache_info()
        with patch('modules.marketplace.bundle_monitoring_views.build_bundle_suggestions', side_effect=AssertionError('No analysis')), \
             patch('modules.marketplace.services.bundle_suggestions.analyze_synthetic', side_effect=AssertionError('No CSV mining')), \
             patch('modules.marketplace.services.bundle_suggestions._cached_synthetic', side_effect=AssertionError('No cache lookup')), \
             patch('modules.marketplace.bundle_monitoring_views.annotated', side_effect=AssertionError('No live query')):
            for actor in (self.root, self.manager):
                self.client.force_login(actor)
                response = self.client.get(reverse('bundle_monitor_list'), {'view': 'dataset', 'run': '1'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['recommendation_view'], 'dataset')
                for label in ('Dataset-Based Recommendations', 'Live Recommendations', 'Synthetic Dataset',
                              'Analyzed Transactions', 'Unique Products', 'Association Rules Found',
                              'Recommended Product Combinations', 'Supporting Transactions',
                              'Saved dataset results unavailable', 'View Dataset &amp; Analysis'):
                    self.assertContains(response, label)
                self.assertContains(response, '<dd>Not available</dd>', count=4, html=True)
                self.assertNotContains(response, 'Saved Bundle Suggestions')
                self.assertNotContains(response, 'Run Demo Analysis')
                self.assertNotContains(response, 'Highlight for Seller')
                self.assertNotContains(response, self.a.name)
                self.assertEqual(response.headers['Cache-Control'], 'private, no-store, max-age=0, no-cache, must-revalidate')
        self.assertEqual(_cached_synthetic.cache_info(), cache_before)
        self.assertEqual((BundleRecommendation.objects.count(), AccountActivity.objects.count()), before)

    def test_source_tabs_live_default_filters_and_scope_are_preserved(self):
        from urllib.parse import parse_qs, urlsplit
        for actor in (self.root, self.manager):
            self.client.force_login(actor)
            for view in ('live', 'unknown'):
                response = self.client.get(reverse('bundle_monitor_list'), {'view': view, 'q': self.a.name, 'page': 2})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['recommendation_view'], 'live')
                self.assertEqual(response.context['summary']['total'], 1)
                self.assertContains(response, 'Saved Bundle Suggestions')
                self.assertContains(response, 'Product bundle suggestions generated from actual CampusHub marketplace transactions.')
                self.assertNotContains(response, 'Saved dataset results unavailable')
                args = parse_qs(urlsplit(response.context['dataset_url']).query)
                self.assertEqual(args['q'], [self.a.name])
                self.assertEqual(args['view'], ['dataset'])
                self.assertNotIn('page', args)

    def test_source_tabs_dataset_does_not_bypass_view_permission(self):
        from django.test import RequestFactory
        from .bundle_monitoring_views import suggestion_list
        self.manager.user_permissions.clear()
        actor = User.objects.get(pk=self.manager.pk)
        request = RequestFactory().get('/admin-bundle-suggestions/', {'view': 'dataset'})
        request.user = actor
        with self.assertRaises(PermissionDenied):
            suggestion_list(request)

    def test_optional_source_tab_browser_fixtures(self):
        import os
        from pathlib import Path
        destination = os.environ.get('BUNDLE_SOURCE_PREVIEW_DIR')
        if not destination:
            return
        target = Path(destination)
        target.mkdir(parents=True, exist_ok=True)
        for role, actor in (('super', self.root), ('manager', self.manager)):
            self.client.force_login(actor)
            for source in ('dataset', 'live'):
                response = self.client.get(reverse('bundle_monitor_list'), {'view': source})
                self.assertEqual(response.status_code, 200)
                (target / f'{role}-{source}.html').write_bytes(response.content)

    def test_workspace_evidence_missing_and_database_error_are_unknown(self):
        from .services.bundle_monitoring import workspace_analysis_summary, saved_analysis_summary
        before = AccountActivity.objects.count()
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', side_effect=AssertionError('No mining')):
            for actor in (self.root, self.manager):
                data = workspace_analysis_summary(actor)
                self.assertEqual(data['state'], 'unrecorded')
                for key in ('basket_count', 'multi_item_basket_count', 'completed_at', 'completed_label', 'rule_count'):
                    self.assertIsNone(data[key])
                self.assertEqual(data['source_label'], 'Not recorded')
            self.assertIsNone(saved_analysis_summary(self.root))
        with patch('modules.marketplace.services.bundle_monitoring.AccountActivity.objects.filter', side_effect=DatabaseError('private')):
            data = workspace_analysis_summary(self.manager)
        self.assertEqual(data['state'], 'unavailable')
        self.assertEqual(data['rules_state'], 'unavailable')
        self.assertNotIn('private', str(data))
        self.assertEqual(AccountActivity.objects.count(), before)
        with self.assertRaises(PermissionDenied):
            workspace_analysis_summary(User.objects.create_user(username='no-evidence-access'))

    def test_workspace_evidence_validates_exact_saved_scope_and_preserves_dashboard_keys(self):
        from .services.bundle_monitoring import workspace_analysis_summary, saved_analysis_summary
        base = {'analysis_version': 1, 'run_id': '8d66cc69-2cd6-40e0-a46f-95fb006c7071',
                'source': 'live', 'completed_at': '2026-10-25T18:30:00+00:00',
                'analysis_scope': 'marketplace', 'basket_count': 0, 'multi_item_basket_count': 0,
                'recommendation_count': 0, 'outcome': 'insufficient_data',
                'scope': {'kind': 'program', 'program_id': self.program.pk, 'major_id': None}}
        target = 'modules.marketplace.services.bundle_monitoring.AccountActivity.objects.filter'
        with patch(target) as query:
            query.return_value.order_by.return_value.first.return_value = SimpleNamespace(metadata=base)
            data = workspace_analysis_summary(self.manager)
            self.assertEqual((data['basket_count'], data['multi_item_basket_count']), (0, 0))
            self.assertIn('Oct 26, 2026', data['completed_label'])
            self.assertIn('2:30 AM', data['completed_label'])
            self.assertIsNone(data['rule_count'])
            old = saved_analysis_summary(self.manager)
            self.assertNotIn('multi_item_basket_count', old)
            self.assertNotIn('rule_count', old)
            self.assertEqual(set(old), {'state', 'basket_count', 'completed_at', 'completed_label', 'source_label', 'history_label', 'note', 'scope_note'})
            for changes in ({'source': 'synthetic'}, {'analysis_version': True}, {'run_id': 'bad'},
                            {'scope': []}, {'scope': {'kind': 'global', 'program_id': None, 'major_id': None}},
                            {'scope': {**base['scope'], 'program_id': True}},
                            {'basket_count': True}, {'multi_item_basket_count': 1},
                            {'completed_at': '2026-10-25T18:30:00'}, {'outcome': 'invented'},
                            {'recommendation_count': 1}):
                with self.subTest(changes=changes):
                    query.return_value.order_by.return_value.first.return_value = SimpleNamespace(metadata={**base, **changes})
                    self.assertEqual(workspace_analysis_summary(self.manager)['state'], 'unrecorded')
            for metadata in (None, [], 'bad'):
                query.return_value.order_by.return_value.first.return_value = SimpleNamespace(metadata=metadata)
                self.assertEqual(workspace_analysis_summary(self.manager)['state'], 'unrecorded')
            for actor, scope in ((self.root, {'kind': 'global', 'program_id': None, 'major_id': None}),
                                 (self.manager, base['scope'])):
                query.return_value.order_by.return_value.first.return_value = SimpleNamespace(metadata={
                    **base, 'scope': scope, 'outcome': 'no_recommendations', 'basket_count': 10, 'multi_item_basket_count': 5})
                data = workspace_analysis_summary(actor)
                self.assertEqual(data['state'], 'no_recommendations')
                self.assertIsNone(data['rule_count'])
                self.assertEqual(data['rules_state'], 'not_recorded')
                self.assertNotIn('no rules', data['rules_note'].lower())
                self.assertEqual(query.call_args.kwargs['metadata__scope__kind'], scope['kind'])

    def test_workspace_reads_saved_major_global_and_source_without_scope_fallback(self):
        from .services.bundle_monitoring import workspace_analysis_summary, ANALYSIS_COMPLETED
        program, _ = Department.objects.get_or_create(code='BTLED', defaults={'name': 'Teacher Education', 'is_program': True})
        major = ProgramMajor.objects.create(program=program, code='EVIDENCE', name='Evidence')
        self.manager.department = program
        self.manager.major = major
        self.manager.save(update_fields=['department', 'major'])
        base = {'analysis_version': 1, 'run_id': '8d66cc69-2cd6-40e0-a46f-95fb006c7071',
                'source': 'live', 'completed_at': '2026-10-25T18:30:00+00:00',
                'analysis_scope': 'marketplace', 'basket_count': 12, 'multi_item_basket_count': 4,
                'recommendation_count': 1, 'outcome': 'recommendations'}
        def event(scope, **changes):
            AccountActivity.objects.create(module='Marketplace', result=AccountActivity.RESULT_SUCCESS,
                activity_type=ANALYSIS_COMPLETED, activity='Isolated evidence',
                metadata={**base, 'scope': scope, **changes})
        event({'kind': 'global', 'program_id': None, 'major_id': None})
        event({'kind': 'program', 'program_id': self.program.pk, 'major_id': None})
        self.assertEqual(workspace_analysis_summary(self.manager)['state'], 'unrecorded')
        scope = {'kind': 'major', 'program_id': program.pk, 'major_id': major.pk}
        event(scope, basket_count=3, multi_item_basket_count=1)
        event(scope, source='synthetic', basket_count=999)
        before = (AccountActivity.objects.count(), BundleRecommendation.objects.count(), Product.objects.count())
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', side_effect=AssertionError('No mining')):
            data = workspace_analysis_summary(self.manager)
            self.assertEqual((data['basket_count'], data['multi_item_basket_count']), (3, 1))
            self.assertEqual(workspace_analysis_summary(self.root)['basket_count'], 12)
        self.assertEqual(before, (AccountActivity.objects.count(), BundleRecommendation.objects.count(), Product.objects.count()))

    def test_recommendation_original_evidence_direction_zero_and_unknown_provenance(self):
        from .services.bundle_monitoring import recommendation_evidence
        self.row.metrics = {'support': 0, 'confidence': 0.0, 'lift': .5,
                            'product_a_id': str(self.b.pk), 'product_b_id': str(self.a.pk)}
        with self.assertNumQueries(0):
            data = recommendation_evidence(self.row)
        self.assertEqual(data['state'], 'recorded')
        self.assertEqual((data['antecedent_name'], data['consequent_name']), (self.b.name, self.a.name))
        self.assertEqual((data['support'], data['confidence'], data['lift']), (0, 0, .5))
        for key in ('supporting_basket_count', 'analysis_run_at', 'source_label'):
            self.assertIsNone(data[key])
        self.assertEqual(data['evidence_label'], 'Original stored evidence')
        self.assertIn('not latest verification', data['note'])

    def test_recommendation_evidence_rejects_malformed_metrics_and_foreign_ids(self):
        from .services.bundle_monitoring import recommendation_evidence
        base = {'support': 100, 'confidence': 100, 'lift': 2,
                'product_a_id': self.a.pk, 'product_b_id': self.b.pk}
        invalid = [None, [], 'bad', {}, {**base, 'product_a_id': 999999},
                   {**base, 'product_a_id': self.b.pk}, {**base, 'product_a_id': True},
                   {**base, 'product_a_id': float(self.a.pk)}, {**base, 'product_a_id': 'live:1'},
                   {**base, 'product_a_id': '0' + str(self.a.pk)}]
        for key in ('support', 'confidence', 'lift'):
            for value in (True, False, None, '25', float('nan'), float('inf'), -1, 10 ** 400):
                invalid.append({**base, key: value})
        invalid.extend([{**base, 'support': 101}, {**base, 'confidence': 101}, {**base, 'lift': 0}])
        for metrics in invalid:
            with self.subTest(metrics=metrics):
                self.row.metrics = metrics
                data = recommendation_evidence(self.row)
                self.assertEqual(data['state'], 'unavailable')
                self.assertIsNone(data['support'])
                self.assertIsNone(data['antecedent_name'])

    def test_marketplace_workspace_sections_empty_history_and_no_mining(self):
        self.client.force_login(self.manager)
        before = (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count())
        with patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', side_effect=AssertionError('GET must not mine')):
            response = self.client.get(reverse('bundle_monitor_list'))
        self.assertEqual(response.status_code, 200)
        for heading in ('Recommendation Overview', 'Apriori Analysis Summary', 'Frequently Bought Together', 'Saved Bundle Suggestions', 'Excel Analysis Export'):
            self.assertContains(response, heading)
        self.assertContains(response, 'Historical analysis information unavailable')
        self.assertContains(response, 'Analysis history not recorded')
        self.assertContains(response, 'data-bundle-detail')
        self.assertContains(response, 'Export is unavailable')
        self.assertNotContains(response, 'download=')
        self.assertIsNone(response.context['analysis']['rule_count'])
        self.assertEqual(response.context['summary'], {'total': 1, 'sent': 0, 'created': 0, 'awaiting': 0})
        self.assertEqual(before, (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count()))

    def test_workspace_empty_saved_and_filtered_states_ignore_incidental_parameters(self):
        self.client.force_login(self.manager)
        url = reverse('bundle_monitor_list')
        response = self.client.get(url, {'q': 'missing'})
        self.assertContains(response, 'No Matching Suggestions')
        self.assertEqual(response.context['summary']['total'], 1)
        self.row.delete()
        for params in ({}, {'page': '2'}, {'q': ''}, {'__at': 'irrelevant'}, {'q': 'missing'}):
            response = self.client.get(url, params)
            self.assertContains(response, 'No Saved Bundle Suggestions Yet')
            self.assertContains(response, 'Saved product recommendations will appear here when available.')
            self.assertNotContains(response, 'No Matching Suggestions')

    def test_workspace_recorded_zero_counts_manila_dates_and_unknown_raw_rules(self):
        from .services.bundle_monitoring import ANALYSIS_COMPLETED
        AccountActivity.objects.create(module='Marketplace', result=AccountActivity.RESULT_SUCCESS,
            activity_type=ANALYSIS_COMPLETED, activity='Isolated completed analysis', metadata={
                'analysis_version': 1, 'run_id': '8d66cc69-2cd6-40e0-a46f-95fb006c7071', 'source': 'live',
                'completed_at': '2026-10-25T18:30:00+00:00', 'analysis_scope': 'marketplace',
                'scope': {'kind': 'program', 'program_id': self.program.pk, 'major_id': None},
                'basket_count': 0, 'multi_item_basket_count': 0, 'recommendation_count': 0, 'outcome': 'insufficient_data'})
        self.client.force_login(self.manager)
        response = self.client.get(reverse('bundle_monitor_list'))
        self.assertContains(response, 'Marketplace Orders')
        self.assertContains(response, 'Oct 26, 2026 · 2:30 AM PHT')
        self.assertNotContains(response, 'PHT PHT')
        self.assertContains(response, 'Insufficient transaction-basket data')
        self.assertEqual((response.context['analysis']['basket_count'], response.context['analysis']['multi_item_basket_count']), (0, 0))
        self.assertIsNone(response.context['analysis']['rule_count'])
        self.assertContains(response, 'Raw rule count not recorded')

    def test_workspace_drawer_fragment_original_evidence_history_and_fallback_are_readonly(self):
        from django.utils import timezone
        self.row.metrics = {'product_a_id': self.b.pk, 'product_b_id': self.a.pk,
                            'support': 0, 'confidence': 0, 'lift': 1.25}
        self.row.save(update_fields=['metrics'])
        record_event(SimpleNamespace(user=self.manager, META={}), self.row,
                     'BUNDLE_SUGGESTION_GENERATED', 'Recorded test generation.')
        self.client.force_login(self.manager)
        url = reverse('bundle_monitor_detail', args=[self.row.pk])
        before = (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count())
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', side_effect=AssertionError('Details must not mine')):
            response = self.client.get(url, {'format': 'drawer'})
            fallback = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('private, no-store', response['Cache-Control'])
        self.assertNotContains(response, '<!doctype')
        self.assertNotContains(response, '<form')
        for text in ('Association Evidence', 'Original stored', '0.00%', '1.25', 'Recorded test generation.', 'PHT'):
            self.assertContains(response, text)
        self.assertContains(response, '<dt>Antecedent (IF)</dt><dd>Test Cookie</dd>', html=True)
        self.assertContains(response, '<dt>Consequent (THEN)</dt><dd>Test Coffee</dd>', html=True)
        self.assertContains(response, 'Not recorded separately')
        self.assertContains(response, reverse('bundle_monitor_section', args=[self.row.pk, 'response']))
        self.assertContains(fallback, 'Association Evidence')
        self.assertEqual(before, (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count()))

    def test_workspace_drawer_denies_cross_scope_regular_and_mutating_requests(self):
        url = reverse('bundle_monitor_detail', args=[self.row.pk])
        self.assertEqual(self.client.get(url, {'format': 'drawer'}).status_code, 200)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.post(url, {'format': 'drawer'}).status_code, 405)
        self.assertEqual(self.client.get(reverse('bundle_monitor_section', args=[self.row.pk, 'history']), {'format': 'drawer'}).status_code, 404)
        self.a.department = self.other
        self.a.save(update_fields=['department'])
        self.assertEqual(self.client.get(url, {'format': 'drawer'}).status_code, 404)
        regular = User.objects.create_user(username='drawer-no-access')
        self.client.force_login(regular)
        self.assertEqual(self.client.get(url, {'format': 'drawer'}).status_code, 403)

    def test_workspace_does_not_add_sections_to_super_monitor_or_research(self):
        for url in (reverse('bundle_monitor_list'), reverse('bundle_monitor_research')):
            response = self.client.get(url)
            for text in ('Apriori Analysis Summary', 'Excel Analysis Export'):
                self.assertNotContains(response, text)
            if url == reverse('bundle_monitor_list'):
                self.assertContains(response, 'bundleDetailsDrawer')
            else:
                self.assertNotContains(response, 'bundleDetailsDrawer')

    def test_phase2_naming_and_empty_states_for_both_roles(self):
        url = reverse('bundle_monitor_list')
        for actor in (self.root, self.manager):
            self.client.force_login(actor)
            listing = self.client.get(url)
            for label in ('<h1>Bundle Recommendations</h1>', 'Saved Bundle Suggestions',
                          'Review suggested product combinations and seller responses across the marketplace.',
                          'View Dataset &amp; Analysis'):
                self.assertContains(listing, label)
            for params in ({'q': 'missing'}, {'response': 'created'}, {'seller': 'invalid'}):
                response = self.client.get(url, params)
                self.assertContains(response, 'No Matching Suggestions')
                self.assertContains(response, 'Try a different search or reset your filters.')
                self.assertEqual(response.context['summary']['total'], 1)
        self.row.delete()
        for actor in (self.root, self.manager):
            self.client.force_login(actor)
            for params in ({}, {'page': '1'}, {'page': '99', 'unrelated': '1'},
                           {'q': '   ', 'response': '   '}, {'q': 'missing'}):
                response = self.client.get(url, params)
                self.assertContains(response, 'No Saved Bundle Suggestions Yet')
                self.assertContains(response, 'Saved product recommendations will appear here when available.')
                self.assertNotContains(response, 'No Matching Suggestions')
                self.assertFalse(response.context['has_active_filters'] if not params.get('q', '').strip() else False)

    def test_phase2_super_drawer_recorded_evidence_and_no_highlight(self):
        self.row.metrics = {'product_a_id': self.b.pk, 'product_b_id': self.a.pk,
                            'support': 25, 'confidence': 80, 'lift': 2}
        self.row.save(update_fields=['metrics'])
        record_event(SimpleNamespace(user=self.manager, META={}), self.row,
                     'BUNDLE_SUGGESTION_GENERATED', 'Original recorded history.')
        url = reverse('bundle_monitor_detail', args=[self.row.pk])
        response = self.client.get(url, {'format': 'drawer'})
        for value in ('Test Coffee', 'Test Cookie', 'Seller Example', self.program.code,
                      '25.00%', '80.00%', '2.00', 'Original recorded history.', 'PHT'):
            self.assertContains(response, value)
        self.assertIn('private, no-store', response['Cache-Control'])
        self.assertNotContains(response, '<form')
        self.assertNotContains(response, 'Review Seller Highlight')
        self.assertContains(self.client.get(url), 'Association Evidence')
        self.assertEqual(self.client.post(reverse('bundle_monitor_highlight', args=[self.row.pk])).status_code, 403)

    def test_phase2_readonly_analysis_never_executes_or_caches(self):
        from contextlib import ExitStack
        from .services.bundle_suggestions import _cached_synthetic
        before = (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count())
        self.client.force_login(self.manager)
        cache_before = _cached_synthetic.cache_info()
        with ExitStack() as stack:
            for target in ('modules.marketplace.bundle_monitoring_views.build_bundle_suggestions',
                           'modules.marketplace.services.bundle_monitoring.build_bundle_suggestions',
                           'modules.marketplace.services.bundle_suggestions.calculate_market_basket',
                           'modules.marketplace.services.bundle_suggestions._cached_synthetic',
                           'modules.marketplace.bundle_monitoring_views.Path.open'):
                stack.enter_context(patch(target, side_effect=AssertionError('Read-only must not execute/read CSV')))
            for params in ({}, {'tab': 'results'}, {'tab': 'dataset'}, {'tab': 'synthetic'},
                           {'source': 'synthetic', 'refresh': '1'}, {'run': '1', 'page': '1'}):
                response = self.client.get(reverse('bundle_monitor_research'), params)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['mode'], 'analysis_readonly')
                self.assertContains(response, 'Marketplace Orders')
                self.assertContains(response, 'Synthetic Demo')
                self.assertNotContains(response, 'Run Demo Analysis')
                self.assertNotContains(response, 'Highlight for Seller')
                self.assertNotContains(response, 'bm-action-form')
                if params.get('tab') == 'synthetic':
                    self.assertContains(response, 'Saved demo analysis unavailable')
                    self.assertEqual(response.context['rows'], [])
                else:
                    self.assertContains(response, 'Historical dataset unavailable')
                    self.assertEqual([r['item']['id'] for r in response.context['rows']], [self.row.pk])
        self.assertEqual(_cached_synthetic.cache_info(), cache_before)
        self.assertEqual(before, (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count()))
        self.assertEqual(self.client.post(reverse('bundle_monitor_research')).status_code, 405)
        self.assertEqual(self.client.post(reverse('bundle_monitor_research_run')).status_code, 403)
        with self.assertRaises(PermissionDenied):
            refresh_live(self.manager)

    def test_phase2_analysis_and_list_major_isolation_and_super_global_visibility(self):
        program, _ = Department.objects.get_or_create(code='BTLED', defaults={'name': 'Teacher Education', 'is_program': True})
        majors = [ProgramMajor.objects.create(program=program, code=code, name=code) for code in ('M1', 'M2')]
        other_seller = CampusHubUser.objects.create(username='other-major-seller', first_name='Other', last_name='Major',
            email='other-major@example.test', password_hash='unused', department=program, major=majors[1])
        products = [Product.objects.create(mobile_seller=other_seller, department=program, major=majors[1],
            name=name, price=10, stock=10, approval_status='approved') for name in ('Private A', 'Private B')]
        other_row = BundleRecommendation.objects.create(product_a=products[0], product_b=products[1])
        self.manager.department, self.manager.major = program, majors[0]
        self.manager.save(update_fields=['department', 'major'])
        for actor, expected in ((self.manager, set()), (self.root, {self.row.pk, other_row.pk})):
            self.client.force_login(actor)
            listing = self.client.get(reverse('bundle_monitor_list'))
            self.assertEqual({r['id'] for r in listing.context['rows']}, expected)
            detail = self.client.get(reverse('bundle_monitor_detail', args=[other_row.pk]), {'format': 'drawer'})
            self.assertEqual(detail.status_code, 200 if actor == self.root else 404)
            if actor == self.manager:
                for params in ({}, {'program': program.pk, 'major': majors[1].pk}, {'seller': other_seller.owner_ref} if hasattr(other_seller, 'owner_ref') else {'q': 'Private'}, {'tab': 'synthetic'}):
                    analysis = self.client.get(reverse('bundle_monitor_research'), params)
                    self.assertEqual(analysis.status_code, 200)
                    self.assertEqual(analysis.context['rows'], [])
                    self.assertNotContains(analysis, 'other-major-seller')
                    self.assertNotContains(analysis, 'Private A')
        self.manager.major = majors[1]
        self.manager.save(update_fields=['major'])
        self.client.force_login(self.manager)
        analysis = self.client.get(reverse('bundle_monitor_research'))
        self.assertEqual([r['item']['id'] for r in analysis.context['rows']], [other_row.pk])
        self.assertNotContains(analysis, 'Test Coffee')

    def test_phase2_facilities_anonymous_and_missing_permission_denied(self):
        facilities = User.objects.create_user(username='phase2-facilities', role='Facilities Admin', is_staff=True)
        facilities.user_permissions.add(Permission.objects.get(codename='can_view_marketplace_analytics'))
        unprivileged = User.objects.create_user(username='phase2-no-permission', role='Marketplace Admin', is_staff=True, department=self.program)
        unprivileged.groups.clear()
        unprivileged.user_permissions.clear()
        for actor in (None, facilities, unprivileged):
            self.client.logout() if actor is None else self.client.force_login(actor)
            for name, args in (('bundle_monitor_list', []), ('bundle_monitor_research', []),
                               ('bundle_monitor_detail', [self.row.pk])):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403)

    @override_settings(TIME_ZONE='UTC')
    def test_phase2_generated_range_validation_and_manila_boundary(self):
        from datetime import datetime, timezone as dt_timezone
        from django.utils import timezone
        stamp = datetime(2026, 10, 26, 19, 30, tzinfo=dt_timezone.utc)
        BundleRecommendation.objects.filter(pk=self.row.pk).update(generated_at=stamp, sent_at=stamp)
        event = record_event(SimpleNamespace(user=self.manager, META={}), self.row,
                             'BUNDLE_SUGGESTION_HIGHLIGHTED', 'Timestamp event.')
        AccountActivity.objects.filter(pk=event.pk).update(created_at=stamp)
        for actor in (self.root, self.manager):
            self.client.force_login(actor)
            with timezone.override('UTC'):
                response = self.client.get(reverse('bundle_monitor_list'), {'start': '2026-10-27', 'end': '2026-10-27'})
                self.assertEqual(len(response.context['rows']), 1)
                self.assertContains(response, 'Oct 27, 2026')
                self.assertContains(response, '3:30 AM PHT')
                response = self.client.get(reverse('bundle_monitor_list'), {'end': '2026-10-26'})
                self.assertEqual(len(response.context['rows']), 0)
                for section in ('details', 'response', 'history'):
                    response = self.client.get(reverse('bundle_monitor_section', args=[self.row.pk, section]))
                    self.assertContains(response, '3:30 AM PHT')
                activity = self.client.get(reverse('bundle_monitor_activity'))
                self.assertContains(activity, '3:30 AM PHT')
                invalid = self.client.get(reverse('bundle_monitor_list'), {'start': '2026-10-28', 'end': '2026-10-27'})
                self.assertContains(invalid, 'Generated from must be on or before Generated through.')
                self.assertEqual(len(invalid.context['rows']), 0)
                self.assertEqual(invalid.context['summary']['total'], 1)

    def test_phase2_filtered_pagination_stays_server_side(self):
        for index in range(22):
            product = Product.objects.create(mobile_seller=self.seller, department=self.program,
                name=f'Paging {index}', price=10, stock=10, approval_status='approved')
            BundleRecommendation.objects.create(product_a=self.a, product_b=product)
        for actor in (self.root, self.manager):
            self.client.force_login(actor)
            response = self.client.get(reverse('bundle_monitor_list'), {'q': 'Paging', 'response': 'na', 'page': '2'})
            self.assertEqual(response.context['current'].number, 2)
            self.assertEqual(response.context['current'].paginator.count, 22)
            self.assertEqual(len(response.context['rows']), 2)
            self.assertEqual(response.context['summary']['total'], 23)
            self.assertIn('q=Paging', response.context['query_args'])
            self.assertIn('response=na', response.context['query_args'])
            if actor == self.manager:
                evidence = self.client.get(reverse('bundle_monitor_research'), {'q': 'Paging', 'page': '2'})
                self.assertEqual(evidence.context['current'].paginator.count, 22)
                self.assertEqual(len(evidence.context['rows']), 2)
                self.assertIn('q=Paging', evidence.context['query_args'])

    def test_phase2_readonly_analysis_error_is_not_successful_empty_state(self):
        self.client.force_login(self.manager)
        with patch('modules.marketplace.bundle_monitoring_views.recommendations_for', side_effect=DatabaseError('private detail')):
            response = self.client.get(reverse('bundle_monitor_research'))
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, 'Unable to load saved analysis.', status_code=503)
        self.assertNotContains(response, 'private detail', status_code=503)

    def live_result(self):
        # Missing checkout capture is isolated here; the real calculator still mines the baskets.
        mined = calculate_market_basket([[(self.a.pk, self.a.name), (self.b.pk, self.b.name)]] * 3 + [[(99, "Other")]] * 3,
            minimum_support=.02, minimum_confidence=.30, minimum_lift=1, detailed=True, limit=None)
        catalog = {str(p.pk): {"id": p.pk, "name": p.name, "seller_id": p.owner_key,
            "seller": p.owner.get_full_name(), "image_url": ""} for p in (self.a, self.b)}
        # Core uses string product identities in the adapter.
        for rule in mined["rows"]:
            rule["product_a_id"], rule["product_b_id"] = str(rule["product_a_id"]), str(rule["product_b_id"])
        return {"source": "live", "rows": _recommendation_rows(mined, catalog, source="live"), "error": False,
                "transaction_count": 6, "multi_item_count": 3,
                "_analysis_basket_scopes": [{"program_id": self.program.pk, "major_id": None,
                                             "baskets": 6, "multi_item_baskets": 3}]}

    def test_marketplace_dashboard_summary_is_scoped_and_has_one_navigation_action(self):
        from django.utils import timezone
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=['sent_at'])
        outside = CampusHubUser.objects.create(username='other-scope-summary', email='other@example.test', password_hash='unused', department=self.other)
        products = [Product.objects.create(mobile_seller=outside, department=self.other, name=f'Outside summary {i}', price=10) for i in range(2)]
        BundleRecommendation.objects.create(product_a=products[0], product_b=products[1], sent_at=timezone.now())
        self.client.force_login(self.manager)
        before = (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count())
        page = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(page.status_code, 200)
        summary = page.context['bundle_analysis']['dashboard_summary']
        self.assertEqual((summary['sent'], summary['awaiting'], summary['created']), (1, 1, 0))
        self.assertEqual(summary['suggested'], 1)
        html = page.content.decode()
        start = html.index('class="dash-card bundle-dss marketplace-recommendation-summary"')
        panel = html[start:html.index('</section>', start)]
        for label in ('Suggested Product Bundles', 'Saved Suggestions', 'Sent to Sellers', 'Awaiting Seller Response', 'Bundles Created'):
            self.assertIn(label, panel)
        self.assertEqual(panel.count('<a '), 1)
        self.assertIn(reverse('bundle_monitor_list'), panel)
        for label in ('Bundle Recommendations &amp; Activity', '<table', 'Approve Recommendation', 'Reject Recommendation', '>Support<', '>Confidence<', '>Lift<', 'Outside summary'):
            self.assertNotIn(label, panel)
        self.assertEqual((Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count()), before)

    def test_dashboard_rates_use_distinct_sent_recommendations_and_scope(self):
        from django.utils import timezone
        def make_pair(name, sent=True):
            product = Product.objects.create(mobile_seller=self.seller, department=self.program,
                name=name, price=10, stock=20, approval_status='approved')
            return BundleRecommendation.objects.create(product_a=self.a, product_b=product,
                sent_at=timezone.now() if sent else None)
        self.row.sent_at=timezone.now()
        self.row.save(update_fields=['sent_at'])
        second, third, unsent = make_pair('Second'), make_pair('Third'), make_pair('Unsent', False)
        SellerBundleSuggestion.objects.create(seller=self.seller, product_a=self.a, product_b=second.product_b, state='dismissed')
        for index in range(2):
            Product.objects.create(mobile_seller=self.seller, name=f'Created bundle {index}', price=20,
                product_type=Product.TYPE_BUNDLE, source_recommendation=self.row)
        Product.objects.create(mobile_seller=self.seller, name='Unsent bundle', price=20,
            product_type=Product.TYPE_BUNDLE, source_recommendation=unsent)
        outside = User.objects.create_user(username='outside-rate-owner', department=self.other)
        pair = [Product.objects.create(seller=outside, name=f'Outside rate {i}', price=10) for i in range(2)]
        BundleRecommendation.objects.create(product_a=pair[0],product_b=pair[1],sent_at=timezone.now())
        data = activity_summary(self.manager, include_rates=True)
        self.assertEqual(data['rates'], {'sent':3,'responded':2,'created':1,'response_rate':66.7,'creation_rate':33.3})
        self.assertEqual(data['summary']['created'], 3, 'Bundle product count differs from converted recommendations')
        self.assertNotIn('rates', activity_summary(self.root), 'Default callers retain their existing output')
        self.client.force_login(self.manager)
        page = self.client.get(reverse('admin_dashboard_page'))
        self.assertContains(page, '66.7%')
        self.assertContains(page, '33.3%')
        import os
        from pathlib import Path
        if os.environ.get('MARKETPLACE_DASHBOARD_REVIEW_DIR'):
            target = Path(os.environ['MARKETPLACE_DASHBOARD_REVIEW_DIR'])
            target.mkdir(parents=True, exist_ok=True)
            (target / 'recommendation-rates.html').write_bytes(page.content)
        BundleRecommendation.objects.filter(product_a=self.a).update(sent_at=None)
        self.assertEqual(activity_summary(self.manager, include_rates=True)['rates'],
            {'sent':0,'responded':0,'created':0,'response_rate':None,'creation_rate':None})

    def test_marketplace_summary_errors_are_not_zero_or_empty_states(self):
        from django.template.loader import render_to_string
        for actor in (self.manager, self.root):
            with patch('modules.marketplace.services.bundle_monitoring.recommendations_for', side_effect=DatabaseError('private database details')), \
                 patch('modules.marketplace.services.bundle_monitoring.activity_summary', side_effect=DatabaseError('private database details')):
                data = dashboard_bundle_suggestions(actor)
            self.assertEqual(data['dashboard_summary'], {'suggested': None, 'sent': None, 'awaiting': None, 'created': None})
            panel = render_to_string('marketplace/partials/admin_recommendation_summary.html', {'bundle_analysis': data})
            self.assertEqual(panel.count('&mdash;'), 4)
            self.assertNotIn('No Bundle Suggestions Yet', panel)
            self.assertNotIn('No Recommendation Activity Yet', panel)
            self.assertNotIn('private database details', panel)
            self.assertIn('Unable to load recommendation activity', panel)

    def test_marketplace_dashboard_reads_saved_counts_and_audits_without_mining_or_writes(self):
        self.client.force_login(self.manager)
        before = (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count())
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', side_effect=AssertionError('Dashboard must not mine')):
            page = self.client.get(reverse('admin_dashboard_page'))
        data = page.context['marketplace']
        self.assertEqual(data['bundle_analysis']['dashboard_summary'], {'suggested': 1, 'sent': 0, 'awaiting': 0, 'created': 0})
        self.assertEqual(data['total_sales'], '0.00')
        self.assertEqual(data['total_orders'], 0)
        self.assertIn('unsent_recommendations', [r['key'] for r in data['attention_required']['items']])
        self.assertEqual((Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count()), before)
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=self.live_result()):
            highlight(SimpleNamespace(user=self.manager, META={}), self.row.pk)
        self.client.force_login(self.manager)
        page = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(page.context['bundle_analysis']['dashboard_summary']['sent'], 1)
        self.assertEqual(len(page.context['marketplace']['activities']), 1)

    def test_mobile_product_scope_falls_back_to_seller_program_and_major(self):
        from .services.bundle_monitoring import recommendations_for
        program, _ = Department.objects.get_or_create(code='BTLED', defaults={'name': 'Teacher Education', 'is_program': True})
        major, _ = ProgramMajor.objects.get_or_create(program=program, code='ICT', defaults={'name': 'ICT'})
        other, _ = ProgramMajor.objects.get_or_create(program=program, code='HE', defaults={'name': 'Home Economics'})
        self.manager.department, self.manager.major = program, major
        self.manager.save(update_fields=['department', 'major'])
        self.seller.department, self.seller.major = program, major
        self.seller.save(update_fields=['department', 'major'])
        Product.objects.filter(pk__in=[self.a.pk, self.b.pk]).update(department=None, major=None)
        self.assertTrue(recommendations_for(self.manager).filter(pk=self.row.pk).exists())
        # Explicit Product scope takes priority over the seller fallback.
        Product.objects.filter(pk=self.b.pk).update(department=program, major=other)
        self.assertFalse(recommendations_for(self.manager).filter(pk=self.row.pk).exists())
        Product.objects.filter(pk=self.b.pk).update(department=None, major=None)
        self.seller.major = other
        self.seller.save(update_fields=['major'])
        self.assertFalse(recommendations_for(self.manager).filter(pk=self.row.pk).exists())

    def test_dashboard_top_panel_previews_latest_saved_pairs_and_is_readonly(self):
        from django.utils import timezone
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=['sent_at'])
        for index in range(2):
            product = Product.objects.create(mobile_seller=self.seller, department=self.program,
                name=f'Isolated extra item {index}', category='Food', price=10, stock=20, approval_status='approved')
            BundleRecommendation.objects.create(product_a=self.a, product_b=product)
        before = (BundleRecommendation.objects.count(), AccountActivity.objects.count(), Product.objects.count())
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', side_effect=AssertionError('No mining on dashboard GET')):
            page = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(page.status_code, 200)
        self.assertFalse(page.context['bundle_analysis']['monitor_error'])
        self.assertEqual(len(page.context['bundle_analysis']['monitor_rows']), 2)
        html = page.content.decode()
        start = html.index('<aside class="dashboard-summary-aside executive-bundle-panel"')
        panel = html[start:html.index('</aside>', start)]
        self.assertEqual(panel.count('data-recommendation-id='), 2)
        self.assertEqual([row['product_b'] for row in page.context['bundle_analysis']['monitor_rows']],
                         ['Isolated extra item 1', 'Isolated extra item 0'])
        self.assertEqual(page.context['bundle_analysis']['dashboard_summary'], {'suggested': 3, 'sent': 1, 'awaiting': 1, 'created': 0})
        self.assertIn('Test Coffee', panel)
        self.assertIn('Seller Example', panel)
        self.assertNotIn('<dt>Suggested Product Bundles</dt>', panel)
        self.assertIn('Overview of marketplace product bundle recommendations.', panel)
        self.assertNotIn('<dt>', panel)
        self.assertNotIn('Recommendation Activity', panel)
        self.assertNotIn('View Recommendations', panel)
        self.assertNotIn('<a ', panel)
        self.assertNotIn('executive-bundles', html)
        self.assertEqual(html.count('id="marketplaceRecommendationsTitle"'), 1)
        self.assertLess(html.index('id="dashboardAttentionTitle"'), start)
        for text in ('Support', 'Confidence', 'Lift', 'Send to Seller', 'Create Bundle', '<form', 'Active suggestions'):
            self.assertNotIn(text, panel)
        self.assertEqual(before, (BundleRecommendation.objects.count(), AccountActivity.objects.count(), Product.objects.count()))
        self.assertEqual(self.client.get(reverse('bundle_monitor_list')).status_code, 200)
        import os
        from pathlib import Path
        if os.environ.get('DASHBOARD_TOP_REVIEW_DIR'):
            target = Path(os.environ['DASHBOARD_TOP_REVIEW_DIR'])
            target.mkdir(parents=True, exist_ok=True)
            (target/'populated.html').write_bytes(page.content)
        with patch('modules.reports.views.can_view_bundle_suggestions', return_value=False):
            no_panel = self.client.get(reverse('admin_dashboard_page'))
            self.assertNotContains(no_panel, 'executive-bundle-panel')
            if os.environ.get('DASHBOARD_TOP_REVIEW_DIR'):
                (target/'without-panel.html').write_bytes(no_panel.content)

    def test_super_preview_uses_product_images_placeholder_and_saved_response(self):
        from django.template.loader import render_to_string
        from django.utils import timezone
        self.a.image_url = '["/media/isolated-coffee.jpg", "/media/second.jpg"]'
        self.a.save(update_fields=['image_url'])
        template = 'marketplace/partials/super_recommendation_preview.html'
        def panel(name=None):
            html = render_to_string(template, {'bundle_analysis': dashboard_bundle_suggestions(self.root, limit=2)})
            import os
            from pathlib import Path
            if name and os.environ.get('DASHBOARD_TOP_REVIEW_DIR'):
                target = Path(os.environ['DASHBOARD_TOP_REVIEW_DIR'])
                target.mkdir(parents=True, exist_ok=True)
                (target / (name + '.html')).write_text(html, encoding='utf-8')
            return html
        html = panel('unsent')
        self.assertIn('<h2 id="marketplaceRecommendationsTitle">Suggested Product Bundles</h2>', html)
        self.assertEqual(html.count('>Suggested Product Bundles<'), 1)
        self.assertNotIn('superBundleSuggestionsTitle', html)
        self.assertIn('src="/media/isolated-coffee.jpg"', html)
        self.assertNotIn('/media/second.jpg', html)
        self.assertIn('No image available for Test Cookie', html)
        self.assertIn('Seller: Seller Example', html)
        self.assertIn('Not Sent to Seller', html)
        self.assertNotIn('Recommendation Activity', html)
        self.assertNotIn('<dt>', html)
        self.assertNotIn('<a ', html)
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=['sent_at'])
        html = panel('sent')
        self.assertIn('super-recommendation-status">Awaiting Seller Response', html)
        self.assertNotIn('No Recommendation Activity Yet', html)
        SellerBundleSuggestion.objects.create(seller=self.seller, product_a=self.a, product_b=self.b, state='dismissed')
        self.assertIn('super-recommendation-status">Dismissed', panel('dismissed'))
        Product.objects.create(mobile_seller=self.seller, name='Isolated linked bundle', price=35,
            product_type=Product.TYPE_BUNDLE, source_recommendation=self.row)
        html = panel('created')
        self.assertIn('super-recommendation-status">Bundle Created', html)
        self.assertNotIn('<dt>Bundles Created</dt>', html)
        self.assertEqual(dashboard_bundle_suggestions(self.root)['dashboard_summary']['created'], 1)

    def test_super_preview_distinguishes_errors_from_empty_records(self):
        from django.template.loader import render_to_string
        import os
        from pathlib import Path
        def export_page(name):
            directory = os.environ.get('DASHBOARD_TOP_REVIEW_DIR')
            if directory:
                target = Path(directory); target.mkdir(parents=True, exist_ok=True)
                response = self.client.get(reverse('admin_dashboard_page'))
                self.assertEqual(response.status_code, 200)
                (target / (name + '.html')).write_bytes(response.content)
        template = 'marketplace/partials/super_recommendation_preview.html'
        with patch('modules.marketplace.services.bundle_monitoring.recommendations_for', side_effect=DatabaseError('private details')), \
             patch('modules.marketplace.services.bundle_monitoring.activity_summary', side_effect=DatabaseError('private details')):
            data = dashboard_bundle_suggestions(self.root)
            export_page('error')
        html = render_to_string(template, {'bundle_analysis': data})
        self.assertIn('Unable to load bundle suggestions', html)
        self.assertIn('Reload the dashboard to retry.', html)
        for absent in ('No Bundle Suggestions Yet', 'Recommendation Activity', 'private details', '<dt>', '<a '):
            self.assertNotIn(absent, html)
        BundleRecommendation.objects.all().delete()
        html = render_to_string(template, {'bundle_analysis': dashboard_bundle_suggestions(self.root)})
        self.assertIn('No Bundle Suggestions Yet', html)
        self.assertIn('Saved product combinations will appear here when available.', html)
        self.assertNotIn('<dt>Suggested Product Bundles</dt>', html)
        self.assertNotIn('data-recommendation-id=', html)
        self.assertNotIn('View Recommendations', html)
        export_page('empty')

    def test_super_template_limits_saved_previews_to_two_without_mutating_context(self):
        from django.template.loader import render_to_string
        for index in range(2):
            product = Product.objects.create(mobile_seller=self.seller, department=self.program,
                name=f'Isolated limit item {index}', price=10, approval_status='approved')
            BundleRecommendation.objects.create(product_a=self.a, product_b=product)
        data = dashboard_bundle_suggestions(self.root, limit=3)
        ids = [row['id'] for row in data['monitor_rows']]
        self.assertEqual(len(ids), 3)
        html = render_to_string('marketplace/partials/super_recommendation_preview.html', {'bundle_analysis': data})
        self.assertEqual(html.count('data-recommendation-id='), 2)
        for identity in ids[:2]:
            self.assertIn(f'data-recommendation-id="{identity}"', html)
        self.assertNotIn(f'data-recommendation-id="{ids[2]}"', html)
        self.assertEqual([row['id'] for row in data['monitor_rows']], ids)

    def test_listing_is_readonly_and_hides_research_metrics(self):
        before = (BundleRecommendation.objects.count(), AccountActivity.objects.count(), Product.objects.count())
        response = self.client.get(reverse("bundle_monitor_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Coffee + Test Cookie")
        self.assertNotContains(response, "Highlight for Seller")
        self.assertNotContains(response, ">Support<")
        self.assertEqual(before, (BundleRecommendation.objects.count(), AccountActivity.objects.count(), Product.objects.count()))
        self.assertEqual(response.context["summary"], {"total": 1, "sent": 0, "created": 0, "awaiting": 0})

    def test_recommendation_navigation_is_consistent_for_authorized_admins(self):
        import re
        def sidebar(response):
            html = response.content.decode()
            start = html.index('<aside class="sidebar"')
            return html[start:html.index('</aside>', start)]

        before = (BundleRecommendation.objects.count(), AccountActivity.objects.count(), Product.objects.count())
        dashboard = self.client.get(reverse('admin_dashboard_page'))
        self.assertEqual(dashboard.status_code, 200)
        nav = sidebar(dashboard)
        marketplace = nav[nav.index('<!-- Marketplace -->'):nav.index('<!-- User Management -->')]
        self.assertEqual(re.findall(r'<span class="item-label">([^<]+)</span>', marketplace),
                          ['Products', 'Inventory', 'Orders', 'Seller Applications', 'Bundle Suggestions'])
        self.assertIn(reverse('bundle_monitor_list'), nav)
        self.assertContains(dashboard, 'Suggested Product Bundles')
        self.assertNotContains(dashboard, 'class="marketplace-recommendation-action" href="'+reverse('bundle_monitor_list')+'"')

        listing = self.client.get(reverse('bundle_monitor_list'))
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, '<title>Bundle Recommendations | CampusHub</title>', html=True)
        self.assertContains(listing, '<h1>Bundle Recommendations</h1>', html=True)
        self.assertContains(listing, 'Review suggested product combinations and seller responses across the marketplace.')
        self.assertContains(listing, '<span class="breadcrumb-current" aria-current="page">Bundle Suggestions</span>', html=True)
        self.assertContains(listing, '<span class="breadcrumb-text">Marketplace</span>', html=True)
        self.assertIn(reverse('bundle_monitor_list'), sidebar(listing))
        self.assertIn('class="sidebar-item active" aria-current="page"', sidebar(listing))
        self.assertIn('<div class="nav-group open">', sidebar(listing))
        for url in (reverse('bundle_monitor_detail', args=[self.row.pk]), reverse('bundle_monitor_activity')):
            detail = self.client.get(url)
            self.assertEqual(detail.status_code, 200)
            self.assertContains(detail, '<a class="breadcrumb-link" href="'+reverse('bundle_monitor_list')+'">Bundle Suggestions</a>', html=True)
            self.assertIn(reverse('bundle_monitor_list'), sidebar(detail))
            self.assertIn('class="sidebar-item active" aria-current="page"', sidebar(detail))
        for text in ('>Support<', '>Confidence<', '>Lift<', 'Highlight for Seller', 'Approve Recommendation', 'Reject Recommendation'):
            self.assertNotContains(listing, text)

        # Both authorized identities can navigate; this never grants management.
        self.root.role = 'Marketplace Admin'
        self.root.save(update_fields=['role'])
        self.assertIn(reverse('bundle_monitor_list'), sidebar(self.client.get(reverse('bundle_monitor_list'))))

        self.client.force_login(self.manager)
        manager_page = self.client.get(reverse('bundle_monitor_list'))
        self.assertEqual(manager_page.status_code, 200)
        self.assertIn(reverse('bundle_monitor_list'), sidebar(manager_page))
        self.assertIn('<span class="item-label">Bundle Suggestions</span>', sidebar(manager_page))
        self.assertIn('class="sidebar-item active" aria-current="page"', sidebar(manager_page))
        self.assertContains(manager_page, '<h1>Bundle Recommendations</h1>', html=True)
        self.assertEqual(before, (BundleRecommendation.objects.count(), AccountActivity.objects.count(), Product.objects.count()))

    def test_bundle_sidebar_visibility_uses_existing_authorization(self):
        from django.template.loader import render_to_string
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        from django.contrib.auth.context_processors import PermWrapper
        from .services.bundle_suggestions import can_view_bundle_suggestions
        reader = User.objects.create_user(username='bundle-nav-reader', role='Marketplace Admin',
            is_staff=True, department=self.program)
        reader.groups.clear()
        reader.user_permissions.clear()
        outsider = User.objects.create_user(username='bundle-nav-facilities', role='Facilities Admin', is_staff=True)
        outsider.user_permissions.add(Permission.objects.get(codename='can_view_marketplace_analytics'))
        for actor in (reader, outsider, AnonymousUser()):
            request = RequestFactory().get(reverse('bundle_monitor_list'))
            request.user = actor
            sidebar = render_to_string('partials/admin_sidebar.html',
                {'request': request, 'perms': PermWrapper(actor), 'active_page': 'bundle_suggestions'})
            self.assertNotIn(reverse('bundle_monitor_list'), sidebar)
            self.assertFalse(can_view_bundle_suggestions(actor))
            self.client.force_login(actor) if actor.is_authenticated else self.client.logout()
            self.assertEqual(self.client.get(reverse('bundle_monitor_list')).status_code, 403)

    def test_optional_navigation_browser_fixtures(self):
        import os
        from pathlib import Path
        destination = os.environ.get('BUNDLE_NAV_REVIEW_DIR')
        if not destination:
            return
        root = Path(destination)
        root.mkdir(parents=True, exist_ok=True)
        for role, actor in [('super', self.root), ('manager', self.manager)]:
            self.client.force_login(actor)
            for name, url in [('list', reverse('bundle_monitor_list')),
                              ('detail', reverse('bundle_monitor_detail', args=[self.row.pk])),
                              ('activity', reverse('bundle_monitor_activity'))]:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                root.joinpath(role+'-'+name+'.html').write_bytes(response.content)

    def test_stable_detail_response_history_and_bundle_are_readonly(self):
        for section in ("details", "response", "history", "bundle"):
            response = self.client.get(reverse("bundle_monitor_section", args=[self.row.pk, section]))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "Highlight for Seller")
            if section == 'details':
                self.assertContains(response, '<dt>Lift</dt>', html=True)
        self.assertEqual(AccountActivity.objects.count(), 0)
        self.assertEqual(self.client.post(reverse("bundle_monitor_detail", args=[self.row.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("bundle_monitor_detail", args=[987654])).status_code, 404)

    def test_super_admin_cannot_highlight_even_direct_post(self):
        self.assertEqual(self.client.post(reverse("bundle_monitor_highlight", args=[self.row.pk])).status_code, 403)
        self.row.refresh_from_db()
        self.assertIsNone(self.row.sent_at)

    def test_scope_regular_accounts_and_readonly_research(self):
        regular = User.objects.create_user(username="monitor-regular")
        self.client.force_login(regular)
        self.assertEqual(self.client.get(reverse("bundle_monitor_research")).status_code, 403)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("bundle_monitor_research")).status_code, 200)
        self.client.force_login(regular)
        self.assertEqual(self.client.get(reverse("bundle_monitor_list")).status_code, 403)
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("bundle_monitor_detail", args=[self.row.pk])).status_code, 200)
        self.a.department = self.other
        self.a.save(update_fields=["department"])
        self.assertEqual(self.client.get(reverse("bundle_monitor_detail", args=[self.row.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("bundle_monitor_highlight", args=[self.row.pk])).status_code, 404)

    def test_filters_search_and_invalid_dates(self):
        url = reverse("bundle_monitor_list")
        for filters in ({"q": "Cookie"}, {"q": str(self.row.pk)}, {"seller": self.a.owner_ref}, {"program": self.program.pk}, {"response": "na"}):
            response = self.client.get(url, filters)
            self.assertEqual(len(response.context["rows"]), 1)
        for filters in ({"q": "missing"}, {"program": "invalid"}, {"response": "created"}, {"start": "bad-date"}):
            response = self.client.get(url, filters)
            self.assertEqual(len(response.context["rows"]), 0)
            self.assertContains(response, "No Matching Suggestions")

    def test_manager_analysis_reads_only_saved_scope_without_mining_or_cache_effects(self):
        from .services.bundle_suggestions import _cached_synthetic
        self.client.force_login(self.manager)
        before = (AccountActivity.objects.count(), Product.objects.count(), BundleRecommendation.objects.count())
        cache_before = _cached_synthetic.cache_info()
        metadata = {'analysis_version': 1, 'run_id': '8d66cc69-2cd6-40e0-a46f-95fb006c7071',
            'source': 'live', 'completed_at': '2026-10-25T18:30:00+00:00', 'analysis_scope': 'marketplace',
            'basket_count': 17, 'multi_item_basket_count': 0, 'recommendation_count': 0,
            'outcome': 'insufficient_data',
            'scope': {'kind': 'program', 'program_id': self.program.pk, 'major_id': None}}
        AccountActivity.objects.create(account_id=self.root.pk, account_source='admin', result='success', module='Marketplace', activity='Saved test run',
            activity_type='BUNDLE_ANALYSIS_COMPLETED', metadata=metadata)
        # More recent global, foreign-program and synthetic records must not win.
        for scope, source in (({'kind': 'global', 'program_id': None, 'major_id': None}, 'live'),
                              ({'kind': 'program', 'program_id': self.other.pk, 'major_id': None}, 'live'),
                              (metadata['scope'], 'synthetic')):
            AccountActivity.objects.create(account_id=self.root.pk, account_source='admin', result='success', module='Marketplace', activity='Other test run',
                activity_type='BUNDLE_ANALYSIS_COMPLETED', metadata={**metadata, 'basket_count': 999, 'scope': scope, 'source': source})
        with patch('modules.marketplace.bundle_monitoring_views.build_bundle_suggestions', side_effect=AssertionError('No research execution')), \
             patch('modules.marketplace.services.bundle_suggestions.calculate_market_basket', side_effect=AssertionError('No mining')), \
             patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', side_effect=AssertionError('No live execution')):
            for tab in ('marketplace', 'synthetic', 'results', 'dataset'):
                response = self.client.get(reverse('bundle_monitor_research'), {'tab': tab})
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'Run Demo Analysis')
                self.assertNotContains(response, '999')
                if tab != 'synthetic':
                    self.assertEqual(response.context['analysis']['basket_count'], 17)
                    self.assertContains(response, 'Oct 26, 2026')
                    self.assertContains(response, '2:30 AM')
                    self.assertContains(response, 'Test Coffee')
                else:
                    self.assertContains(response, 'Saved demo analysis unavailable')
                    self.assertNotContains(response, 'Test Coffee')
                self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(cache_before, _cached_synthetic.cache_info())
        self.assertEqual((before[0] + 4, *before[1:]),
                         (AccountActivity.objects.count(), Product.objects.count(), BundleRecommendation.objects.count()))
        self.assertEqual(self.client.post(reverse('bundle_monitor_research')).status_code, 405)
        self.assertEqual(self.client.post(reverse('bundle_monitor_research_run')).status_code, 403)

    def test_dismissed_response_reuses_existing_choice_and_audit(self):
        SellerBundleSuggestion.objects.create(seller=self.seller, product_a=self.a, product_b=self.b, state="dismissed")
        response = self.client.get(reverse("bundle_monitor_section", args=[self.row.pk, "response"]))
        self.assertEqual(response.context["item"]["response"], "Dismissed")
        self.assertIsNotNone(response.context["item"]["response_at"])

    def test_marketplace_highlight_is_scoped_revalidated_and_idempotent(self):
        request = SimpleNamespace(user=self.manager, META={})
        with patch("modules.marketplace.services.bundle_monitoring.build_bundle_suggestions", return_value=self.live_result()):
            highlight(request, self.row.pk)
            highlight(request, self.row.pk)
        self.row.refresh_from_db()
        self.assertEqual(self.row.sent_by, self.manager)
        self.assertEqual(AccountActivity.objects.filter(activity_type="BUNDLE_SUGGESTION_HIGHLIGHTED").count(), 1)
        response = self.client.get(reverse("bundle_monitor_list"))
        self.assertEqual(response.context["summary"]["awaiting"], 1)

    def test_stale_highlight_does_not_record_delivery(self):
        with patch("modules.marketplace.services.bundle_monitoring.build_bundle_suggestions", return_value={"rows": [], "error": False}):
            with self.assertRaises(ValidationError):
                highlight(SimpleNamespace(user=self.manager, META={}), self.row.pk)
        self.row.refresh_from_db()
        self.assertIsNone(self.row.sent_at)

    def test_refresh_is_explicit_idempotent_and_preserves_generated_date(self):
        self.row.delete()
        with patch("modules.marketplace.services.bundle_monitoring.build_bundle_suggestions", return_value=self.live_result()):
            self.assertEqual(refresh_live(self.root)["created"], 1)
            first = BundleRecommendation.objects.get()
            self.assertEqual(refresh_live(self.root)["created"], 0)
        first.refresh_from_db()
        self.assertEqual(AccountActivity.objects.filter(activity_type="BUNDLE_SUGGESTION_GENERATED").count(), 1)
        with self.assertRaises(PermissionDenied):
            refresh_live(self.manager)

    def test_completion_records_exact_counts_timestamp_source_and_scope(self):
        import json
        from datetime import datetime, timezone as dt_timezone
        from .services.bundle_monitoring import ANALYSIS_COMPLETED, saved_analysis_summary
        instant = datetime(2026, 10, 17, 19, 10, 15, tzinfo=dt_timezone.utc)
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=self.live_result()), \
             patch('modules.marketplace.services.bundle_monitoring.timezone.now', return_value=instant):
            refresh_live(self.root)
        events = AccountActivity.objects.filter(activity_type=ANALYSIS_COMPLETED)
        keys = [(event.metadata['run_id'], json.dumps(event.metadata['scope'], sort_keys=True)) for event in events]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len({event.metadata['run_id'] for event in events}), 1)
        event = events.get(metadata__scope__kind='program', metadata__scope__program_id=self.program.pk)
        self.assertEqual(event.metadata['basket_count'], 6)
        self.assertEqual(event.metadata['source'], 'live')
        self.assertEqual(event.metadata['outcome'], 'recommendations')
        summary = saved_analysis_summary(self.manager)
        self.assertEqual(summary['basket_count'], 6)
        self.assertEqual(summary['completed_at'], instant.isoformat())
        self.assertEqual(summary['completed_label'], 'Oct 18, 2026 · 3:10 AM')
        self.assertEqual(summary['source_label'], 'Marketplace Orders')
        self.assertNotIn('run_id', json.dumps(summary))

    def test_zero_basket_run_is_completed_without_inventing_suggestions(self):
        from .services.bundle_monitoring import ANALYSIS_COMPLETED, saved_analysis_summary
        result = refresh_live(self.root)
        self.assertEqual((result['current'], result['transactions']), (0, 0))
        self.assertTrue(AccountActivity.objects.filter(activity_type=ANALYSIS_COMPLETED).exists())
        summary = saved_analysis_summary(self.manager)
        self.assertEqual(summary['basket_count'], 0)
        self.assertEqual(summary['state'], 'insufficient_data')
        self.assertIsNotNone(summary['completed_at'])
        self.assertEqual(summary['source_label'], 'Marketplace Orders')

    def test_completed_run_without_qualifying_rules_is_not_unknown_history(self):
        from .services.bundle_monitoring import saved_analysis_summary
        evidence = {**self.live_result(), 'rows': []}
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=evidence):
            refresh_live(self.root)
        summary = saved_analysis_summary(self.manager)
        self.assertEqual((summary['basket_count'], summary['state']), (6, 'no_recommendations'))
        self.assertIn('no qualifying', summary['note'])
        # Saved outcomes describe their run, not subsequently changed thresholds.
        with patch('modules.marketplace.services.analytics.MARKET_BASKET_MIN_ORDERS', 999):
            self.assertEqual(saved_analysis_summary(self.manager)['state'], 'no_recommendations')

    def test_failed_partial_persistence_rolls_back_completions_and_recommendations(self):
        from .services import bundle_monitoring as service
        original = service.log_marketplace_event
        before = self.row.verified_at
        calls = []
        def interrupted(*args, **kwargs):
            calls.append(kwargs['activity_type'])
            if len(calls) == 2:
                raise DatabaseError('Isolated audit persistence failure')
            return original(*args, **kwargs)
        with patch.object(service, 'build_bundle_suggestions', return_value=self.live_result()), \
             patch.object(service, 'log_marketplace_event', side_effect=interrupted):
            with self.assertRaises(DatabaseError):
                refresh_live(self.root)
        self.row.refresh_from_db()
        self.assertEqual(self.row.verified_at, before)
        self.assertEqual(AccountActivity.objects.count(), 0)

    def test_conflicting_run_identity_and_incomplete_counts_cannot_commit(self):
        from uuid import UUID
        from .services.bundle_monitoring import ANALYSIS_COMPLETED
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=self.live_result()), \
             patch('modules.marketplace.services.bundle_monitoring.uuid4', return_value=UUID('11111111-1111-4111-8111-111111111111')):
            refresh_live(self.root)
            count = AccountActivity.objects.filter(activity_type=ANALYSIS_COMPLETED).count()
            with self.assertRaises(ValidationError):
                refresh_live(self.root)
            self.assertEqual(AccountActivity.objects.filter(activity_type=ANALYSIS_COMPLETED).count(), count)
        incomplete = {**self.live_result(), '_analysis_basket_scopes': []}
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=incomplete):
            with self.assertRaises(ValidationError):
                refresh_live(self.root)
        self.assertEqual(AccountActivity.objects.filter(activity_type=ANALYSIS_COMPLETED).count(), count)

    def test_saved_summary_never_falls_back_to_global_other_major_or_synthetic_counts(self):
        import json
        from uuid import uuid4
        from .services.bundle_monitoring import ANALYSIS_COMPLETED, saved_analysis_summary
        btled, _ = Department.objects.get_or_create(code='BTLED', defaults={'name': 'Teacher Education', 'is_program': True})
        ict, _ = ProgramMajor.objects.get_or_create(program=btled, code='ICT', defaults={'name':'ICT'})
        he, _ = ProgramMajor.objects.get_or_create(program=btled, code='HE', defaults={'name':'HE'})
        for product in (self.a, self.b):
            product.department, product.major = btled, ict
            product.save(update_fields=['department', 'major'])
        evidence = {**self.live_result(), 'transaction_count': 12, 'multi_item_count': 7,
            '_analysis_basket_scopes': [
                {'program_id': btled.pk, 'major_id': ict.pk, 'baskets': 4, 'multi_item_baskets': 2},
                {'program_id': btled.pk, 'major_id': he.pk, 'baskets': 5, 'multi_item_baskets': 3},
                {'program_id': self.program.pk, 'major_id': None, 'baskets': 3, 'multi_item_baskets': 2}]}
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=evidence):
            refresh_live(self.root)
        self.manager.department, self.manager.major = btled, ict
        self.manager.save(update_fields=['department','major'])
        self.assertEqual(saved_analysis_summary(self.manager)['basket_count'], 4)
        matching = AccountActivity.objects.get(activity_type=ANALYSIS_COMPLETED,
            metadata__scope__kind='major', metadata__scope__program_id=btled.pk, metadata__scope__major_id=ict.pk)
        synthetic = {**matching.metadata, 'source':'synthetic','run_id':str(uuid4()),'basket_count':999999}
        AccountActivity.objects.create(module='Marketplace', activity_type=ANALYSIS_COMPLETED,
            result='success', metadata=synthetic)
        self.assertEqual(saved_analysis_summary(self.manager)['basket_count'], 4)
        self.assertNotIn('999999', json.dumps(saved_analysis_summary(self.manager)))
        self.manager.major = he
        self.manager.save(update_fields=['major'])
        self.assertEqual(saved_analysis_summary(self.manager)['basket_count'], 5)
        self.manager.major = None
        self.manager.save(update_fields=['major'])
        self.assertEqual(saved_analysis_summary(self.manager)['state'], 'unrecorded')

    def test_history_fallback_permissions_and_dashboard_get_do_not_mine_or_write(self):
        from .services.bundle_monitoring import saved_analysis_summary
        self.assertEqual(saved_analysis_summary(self.manager)['history_label'], 'Analysis history not recorded')
        self.assertIsNone(saved_analysis_summary(self.manager)['completed_at'])
        self.assertIsNone(saved_analysis_summary(self.root))
        denied = User.objects.create_user(username='analysis-summary-denied', role='User')
        with self.assertRaises(PermissionDenied):
            saved_analysis_summary(denied)
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=self.live_result()):
            refresh_live(self.root)
        before = (AccountActivity.objects.count(), BundleRecommendation.objects.count(), Product.objects.count())
        self.client.force_login(self.manager)
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', side_effect=AssertionError('Dashboard must not mine')):
            response = self.client.get(reverse('admin_dashboard_page'))
        self.assertContains(response, 'Analysis Summary')
        self.assertContains(response, 'Marketplace Orders')
        self.assertNotContains(response, '>Support<')
        self.client.force_login(self.root)
        self.assertNotContains(self.client.get(reverse('admin_dashboard_page')), 'marketplaceAnalysisSummaryTitle')
        self.assertEqual(before, (AccountActivity.objects.count(), BundleRecommendation.objects.count(), Product.objects.count()))

    def test_unverifiable_metadata_never_uses_audit_or_recommendation_dates(self):
        from .services.bundle_monitoring import ANALYSIS_COMPLETED, saved_analysis_summary
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=self.live_result()):
            refresh_live(self.root)
        event = AccountActivity.objects.get(activity_type=ANALYSIS_COMPLETED,
            metadata__scope__kind='program', metadata__scope__program_id=self.program.pk)
        original = dict(event.metadata)
        for key, value in [('completed_at','2026-10-17T19:10:15'),('completed_at','invalid'),
                           ('basket_count',-1),('basket_count',True),('run_id','invalid'),
                           ('outcome','interrupted'),('source','synthetic')]:
            with self.subTest(key=key,value=value):
                AccountActivity.objects.filter(pk=event.pk).update(metadata={**original,key:value})
                summary = saved_analysis_summary(self.manager)
                self.assertEqual(summary['state'], 'unrecorded')
                self.assertIsNone(summary['completed_at'])
                self.assertIsNone(summary['basket_count'])
        # A genuine global completion is not a permitted fallback for a scoped reader.
        AccountActivity.objects.filter(pk=event.pk).delete()
        self.assertTrue(AccountActivity.objects.filter(activity_type=ANALYSIS_COMPLETED,metadata__scope__kind='global').exists())
        self.assertEqual(saved_analysis_summary(self.manager)['state'], 'unrecorded')

    def test_optional_analysis_summary_browser_fixtures(self):
        import os
        from pathlib import Path
        destination = os.environ.get('ANALYSIS_SUMMARY_REVIEW_DIR')
        if not destination:
            return
        root = Path(destination)
        root.mkdir(parents=True, exist_ok=True)
        self.client.force_login(self.manager)
        root.joinpath('unrecorded.html').write_bytes(self.client.get(reverse('admin_dashboard_page')).content)
        self.row.is_current = False
        self.row.save(update_fields=['is_current'])
        root.joinpath('empty.html').write_bytes(self.client.get(reverse('admin_dashboard_page')).content)
        self.row.is_current = True
        self.row.save(update_fields=['is_current'])
        unavailable = {'state':'unavailable','basket_count':None,'completed_at':None,
            'source_label':'Unavailable','history_label':'Analysis history unavailable',
            'note':'Unable to load analysis history.'}
        with patch('modules.marketplace.services.bundle_monitoring.saved_analysis_summary', return_value=unavailable):
            root.joinpath('unavailable.html').write_bytes(self.client.get(reverse('admin_dashboard_page')).content)
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=self.live_result()):
            refresh_live(self.root)
        root.joinpath('completed.html').write_bytes(self.client.get(reverse('admin_dashboard_page')).content)
        from django.utils import timezone
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=['sent_at'])
        root.joinpath('sent.html').write_bytes(self.client.get(reverse('admin_dashboard_page')).content)
        self.row.sent_at = None
        self.row.save(update_fields=['sent_at'])
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value={**self.live_result(),'rows':[]}):
            refresh_live(self.root)
        root.joinpath('no-rules.html').write_bytes(self.client.get(reverse('admin_dashboard_page')).content)
        refresh_live(self.root)
        root.joinpath('insufficient.html').write_bytes(self.client.get(reverse('admin_dashboard_page')).content)

    def test_compact_card_missing_history_copy_and_empty_rates_are_presentation_only(self):
        self.row.delete()
        self.client.force_login(self.manager)
        before = (AccountActivity.objects.count(), BundleRecommendation.objects.count(), Product.objects.count())
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', side_effect=AssertionError('Dashboard must not mine')):
            response = self.client.get(reverse('admin_dashboard_page'))
        self.assertContains(response, 'Eligible saved recommendations will appear here.', count=1)
        self.assertContains(response, '<dt>Last Analysis</dt><dd>Not recorded</dd>', html=True)
        self.assertContains(response, '<dt>Data Source</dt><dd>Not recorded</dd>', html=True)
        self.assertContains(response, 'No completed analysis record is available for your scope.', count=1)
        self.assertContains(response, '<dt>Seller Response Rate</dt><dd>&mdash;</dd>', html=True)
        self.assertContains(response, '<dt>Bundle Creation Rate</dt><dd>&mdash;</dd>', html=True)
        self.assertContains(response, 'Rates are unavailable until suggestions are sent.', count=1)
        self.assertNotContains(response, 'No Analysis Yet')
        html = response.content.decode()
        self.assertLess(html.index('Recommendation Activity</h3>'), html.index('Seller response and bundle rates</summary>'))
        self.assertLess(html.index('Seller response and bundle rates</summary>'), html.index('Analysis Summary</h3>'))
        self.assertNotIn('open', html.split('<details class="marketplace-dashboard-details"',1)[1].split('>',1)[0])
        # The existing saved-only data contract is intentionally unchanged.
        self.assertEqual(response.context['bundle_analysis']['analysis_summary']['history_label'], 'Analysis history not recorded')
        self.assertEqual(response.context['bundle_analysis']['analysis_summary']['source_label'], 'No Analysis Yet')
        self.assertEqual(before, (AccountActivity.objects.count(), BundleRecommendation.objects.count(), Product.objects.count()))

    def test_compact_card_preserves_real_zero_rates_and_verified_analysis(self):
        from django.utils import timezone
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=['sent_at'])
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value=self.live_result()):
            refresh_live(self.root)
        self.client.force_login(self.manager)
        response = self.client.get(reverse('admin_dashboard_page'))
        self.assertContains(response, 'Marketplace Orders')
        self.assertContains(response, '0.0%', count=2)
        self.assertContains(response, '0 bundles from 1 sent suggestion.')
        self.assertContains(response, 'Baskets in your scope from the saved marketplace-wide analysis.', count=1)
        self.assertNotContains(response, 'Analysis completed; eligible saved suggestions appear above.')
        self.assertEqual(response.context['bundle_analysis']['dashboard_summary'],
            {'suggested':1,'sent':1,'awaiting':1,'created':0})

    def test_refresh_failure_preserves_existing_evidence(self):
        with patch("modules.marketplace.services.bundle_monitoring.build_bundle_suggestions", return_value={"error": True}):
            with self.assertRaises(ValidationError):
                refresh_live(self.root)
        self.row.refresh_from_db()
        self.assertTrue(self.row.is_current)

    def test_synthetic_rules_cannot_be_persisted_as_live_suggestions(self):
        result = {**self.live_result(), "source": "synthetic"}
        with patch("modules.marketplace.services.bundle_monitoring.build_bundle_suggestions", return_value=result):
            with self.assertRaises(ValidationError):
                refresh_live(self.root)
        self.assertEqual(BundleRecommendation.objects.count(), 1)
        self.assertEqual(AccountActivity.objects.count(), 0)

    def test_real_single_product_checkout_cannot_create_pair(self):
        result = refresh_live(self.root)
        self.assertEqual(result["created"], 0)
        self.row.refresh_from_db()
        self.assertFalse(self.row.is_current)

    def test_created_bundle_is_explicit_link_not_product_name_guess(self):
        bundle = Product.objects.create(mobile_seller=self.seller, department=self.program,
            name="Test Coffee + Test Cookie", price=35, product_type="bundle")
        BundleComponent.objects.create(bundle=bundle, product=self.a, required_quantity=1)
        BundleComponent.objects.create(bundle=bundle, product=self.b, required_quantity=1)
        url = reverse("bundle_monitor_section", args=[self.row.pk, "bundle"])
        self.assertContains(self.client.get(url), "No created bundle recorded")
        link_created_bundle(SimpleNamespace(user=self.root, META={}), bundle, [self.a.pk, self.b.pk])
        response = self.client.get(url)
        self.assertContains(response, "35.00")
        self.assertContains(response, "Test Cookie × 1")
        self.assertEqual(response.context["item"]["response"], "Bundle Created")
        self.assertEqual(AccountActivity.objects.filter(activity_type="BUNDLE_CREATED_FROM_SUGGESTION").count(), 1)

    def test_bundle_breadcrumb_is_once_in_header_with_greater_than_separators(self):
        for name in ('bundle_monitor_list', 'bundle_monitor_research', 'bundle_monitor_activity'):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn('bundle-monitoring admin-module-shell', html)
            header = html.split('<header class="dashboard-header"', 1)[1].split('</header>', 1)[0]
            self.assertIn('aria-label="Breadcrumb"', header)
            self.assertIn('Marketplace', header)
            self.assertIn('Bundle Suggestions', header)
            self.assertIn('href="' + reverse('admin_dashboard_page') + '"', header)
            self.assertIn('<span class="breadcrumb-sep" aria-hidden="true">&gt;</span>', header)
            self.assertIn('class="breadcrumb-link"', header)
            self.assertIn('class="breadcrumb-text">Marketplace', header)
            self.assertIn('class="breadcrumb-current" aria-current="page"', header)
            self.assertEqual(html.count('aria-label="Breadcrumb"'), 1)
            self.assertNotIn('bm-breadcrumb', html)
        from django.template.loader import render_to_string
        fallback = render_to_string('partials/admin_header.html', {
            'page_title': 'Other page', 'breadcrumb_section': 'Reports',
            'breadcrumb_page': 'Analytics',
        }, request=response.wsgi_request)
        self.assertIn('breadcrumb-current">Analytics', fallback)
        self.assertNotIn('Bundle Suggestions', fallback)

    def test_research_reads_csv_but_does_not_touch_live_records(self):
        from .services.bundle_suggestions import build_bundle_suggestions
        before = (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count())
        response = self.client.get(reverse("bundle_monitor_research"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="syntheticNoticeTitle">Synthetic Dataset')
        self.assertNotContains(response, 'Demo Only')
        self.assertContains(response, "Simulated marketplace transactions for Apriori analysis. Not actual customer purchases.")
        self.assertNotContains(response, "This dataset contains simulated marketplace transactions used for research")
        self.assertGreater(response.context["result"]["transaction_count"], 0)
        rules = self.client.get(reverse("bundle_monitor_research"), {"tab": "results"})
        self.assertEqual(rules.status_code, 200)
        for rendered in (response, rules):
            html = rendered.content.decode()
            panel = html.index('<section class="bm-panel bm-research-panel">')
            notice = html.index('<aside class="bm-disclosure"')
            metadata = html.index('<dl class="bm-dataset-stats"')
            tabs = html.index('<nav class="bm-tabs" aria-label="Research views">')
            self.assertLess(html.index('Back to Suggestions'), panel)
            self.assertLess(html.index('<h1>'), panel)
            self.assertLess(panel, notice)
            self.assertLess(notice, metadata)
            self.assertLess(metadata, tabs)
            self.assertIn('</dl>\n<nav class="bm-tabs" aria-label="Research views">', html.replace('\r\n', '\n'))
            self.assertEqual(html.count('class="bm-panel'), 1)
            self.assertEqual(html.count('id="syntheticNoticeTitle"'), 1)
            self.assertEqual(html.count('class="bm-dataset-stats"'), 1)
            self.assertNotContains(rendered, 'class="bm-dataset-details"')
            self.assertNotContains(rendered, 'Dataset Details')
            self.assertContains(rendered, '<dt>Transactions</dt><dd>%s</dd>' % rendered.context['result']['transaction_count'], html=True)
            self.assertContains(rendered, '<dt>Order Items</dt><dd>%s</dd>' % rendered.context['result']['item_count'], html=True)
            self.assertContains(rendered, '<dt>Unique Products</dt><dd>%s</dd>' % rendered.context['distinct_products'], html=True)
            self.assertTrue(rendered.context['filename'])
            self.assertNotContains(rendered, '<dt>File</dt>')
            self.assertNotContains(rendered, '<dt>Data Source</dt>')
            self.assertNotContains(rendered, 'Demo Only')
        expected = build_bundle_suggestions(self.root, source="synthetic")["directional_rows"]
        self.assertEqual(rules.context["current"].paginator.count, len(expected))
        self.assertNotContains(rules, "Highlight for Seller")
        self.assertEqual(before, (Product.objects.count(), BundleRecommendation.objects.count(), AccountActivity.objects.count()))

    @override_settings(CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH="missing-dataset.csv")
    def test_missing_dataset_is_an_error_not_empty_success(self):
        response = self.client.get(reverse("bundle_monitor_research"))
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Dataset unavailable", status_code=503)
        self.assertContains(response, 'class="bm-panel bm-research-panel"', status_code=503)
        self.assertNotContains(response, 'class="bm-dataset-stats"', status_code=503)
        self.assertNotContains(response, 'class="bm-dataset-details"', status_code=503)
        self.assertNotContains(response, 'aria-label="Research views"', status_code=503)

    def test_dashboard_preview_uses_stable_ids_without_internal_objects_or_metrics(self):
        from django.core.serializers.json import DjangoJSONEncoder
        import json
        data = dashboard_bundle_suggestions(self.root, limit=2)
        self.assertEqual(data["monitor_rows"][0]["id"], self.row.pk)
        json.dumps(data, cls=DjangoJSONEncoder)
        self.assertNotIn("metrics", data["monitor_rows"][0])

    def test_generation_alone_is_not_seller_activity(self):
        record_event(SimpleNamespace(user=self.root, META={}), self.row,
            "BUNDLE_SUGGESTION_GENERATED", "Suggestion generated.")
        result = activity_summary(self.root)
        self.assertFalse(result["has_activity"])
        self.assertEqual(result["summary"], {"sent": 0, "awaiting": 0, "created": 0, "dismissed": 0})

    def test_activity_counts_use_records_not_duplicate_audit_events(self):
        from django.utils import timezone
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=["sent_at"])
        request = SimpleNamespace(user=self.manager, META={})
        for _ in range(2):
            record_event(request, self.row, "BUNDLE_SUGGESTION_HIGHLIGHTED", "Suggestion highlighted.")
        for name in ("First real test bundle", "Second real test bundle"):
            Product.objects.create(name=name, mobile_seller=self.seller, price=35,
                product_type="bundle", source_recommendation=self.row)
        result = activity_summary(self.root)
        self.assertEqual(result["summary"], {"sent": 1, "awaiting": 0, "created": 2, "dismissed": 0})
        self.assertTrue(result["has_activity"])
        response = self.client.get(reverse("bundle_monitor_activity"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["rows"]), 2)
        self.assertContains(response, reverse("bundle_monitor_detail", args=[self.row.pk]))
        self.assertNotContains(response, "Highlight for Seller")

    def test_legacy_seller_action_is_correlated_to_exact_owner_pair(self):
        from accounts.activity_logging import log_marketplace_event
        log_marketplace_event(SimpleNamespace(user=self.root, META={}), account=self.seller, source="mobile",
            activity_type="BUNDLE_SUGGESTION_UPDATED", activity="Suggestion saved.",
            metadata={"product_ids": [self.a.pk, self.b.pk]})
        self.assertEqual(activity_events_for(self.root).count(), 1)
        self.assertTrue(activity_summary(self.root)["has_activity"])
        self.client.force_login(self.manager)
        self.a.department = self.other
        self.a.save(update_fields=["department"])
        self.assertFalse(activity_events_for(self.manager).exists())
        response = self.client.get(reverse("bundle_monitor_activity"))
        self.assertNotContains(response, "Suggestion saved.")

    def test_dismissal_and_unanswered_highlight_are_independent_counts(self):
        from django.utils import timezone
        self.row.sent_at = timezone.now()
        self.row.save(update_fields=["sent_at"])
        self.assertEqual(activity_summary(self.root)["summary"]["awaiting"], 1)
        SellerBundleSuggestion.objects.create(seller=self.seller, product_a=self.a, product_b=self.b, state="dismissed")
        result = activity_summary(self.root)
        self.assertEqual(result["summary"], {"sent": 1, "awaiting": 0, "created": 0, "dismissed": 1})

    def test_activity_view_has_distinct_error_and_authorization_states(self):
        url = reverse("bundle_monitor_activity")
        self.assertEqual(self.client.post(url).status_code, 405)
        with patch("modules.marketplace.bundle_monitoring_views.activity_summary", side_effect=DatabaseError):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, "No Recommendation Activity Yet", status_code=503)
        self.assertContains(response, f'href="{url}" class="bm-button">Retry', status_code=503)
        regular = User.objects.create_user(username="activity-regular")
        self.client.force_login(regular)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_csrf_required_for_highlighting(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        self.assertEqual(client.post(reverse("bundle_monitor_highlight", args=[self.row.pk])).status_code, 403)

    def test_research_rerun_is_super_only_post_and_never_persists(self):
        url = reverse("bundle_monitor_research_run")
        self.assertEqual(self.client.get(url).status_code, 405)
        before = (BundleRecommendation.objects.count(), Product.objects.count(), AccountActivity.objects.count())
        self.assertEqual(self.client.post(url, follow=True).status_code, 200)
        self.assertEqual(before, (BundleRecommendation.objects.count(), Product.objects.count(), AccountActivity.objects.count()))
        self.client.force_login(self.manager)
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_optional_isolated_render_fixtures(self):
        import os
        from pathlib import Path
        destination = os.environ.get("BUNDLE_MONITOR_PREVIEW_DIR")
        if not destination:
            return
        root = Path(destination)
        root.mkdir(parents=True, exist_ok=True)
        paths = {"index.html": reverse("bundle_monitor_list"), "details.html": reverse("bundle_monitor_detail", args=[self.row.pk]),
            "response.html": reverse("bundle_monitor_section", args=[self.row.pk, "response"]),
            "history.html": reverse("bundle_monitor_section", args=[self.row.pk, "history"]),
            "bundle.html": reverse("bundle_monitor_section", args=[self.row.pk, "bundle"]),
            "dataset.html": reverse("bundle_monitor_research"), "results.html": reverse("bundle_monitor_research") + "?tab=results",
            "activity.html": reverse("bundle_monitor_activity")}
        for filename, url in paths.items():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            html = response.content.decode().replace('/static/', 'http://127.0.0.1:8000/static/')
            html = html.replace('<main class="bm-page" id="bundleMain">', '<main class="bm-page" id="bundleMain"><p class="bm-note">Isolated test preview. Product records shown here are test fixtures, not live marketplace data.</p>')
            for target, route in sorted(paths.items(), key=lambda pair: -len(pair[1])):
                html = html.replace('href="' + route + '"', 'href="' + target + '"')
            html = html.replace('href="?tab=dataset"', 'href="dataset.html"').replace('href="?tab=results"', 'href="results.html"')
            (root / filename).write_text(html, encoding="utf-8")

    def test_marketplace_dashboard_previews_only_eligible_saved_pairs_without_mining(self):
        from modules.reports.views import _marketplace_operational_dashboard_data
        from django.test import RequestFactory
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', side_effect=AssertionError('Dashboard must not mine')):
            data = dashboard_bundle_suggestions(self.manager)
            self.assertEqual([row['id'] for row in data['monitor_rows']], [self.row.pk])
            request = RequestFactory().get('/admin-dashboard/')
            request.user = self.manager
            self.assertEqual(_marketplace_operational_dashboard_data(request,self.manager)['bundle_analysis']['monitor_rows'][0]['id'],self.row.pk)
        self.b.is_archived=True;self.b.save(update_fields=['is_archived'])
        self.assertEqual(dashboard_bundle_suggestions(self.manager)['monitor_rows'], [])
