"""Real PostgreSQL decisions and submissions in Django's disposable test database."""
import json
from unittest.mock import patch
from django.test import TestCase
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from accounts.models import AccountActivity, User
from api.models import BundleRecommendation, CampusHubUser, Product, SellerBundleSuggestion
from api.tests import test_mobile_seller_workspace as fixtures
from modules.marketplace.services.bundle_monitoring import presentation, activity_summary


class AdminSellerRecommendationTests(TestCase):
    account = fixtures.MobileSellerWorkspaceTests.account
    product = fixtures.MobileSellerWorkspaceTests.product
    setUp = fixtures.MobileSellerWorkspaceTests.setUp

    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def sent(self):
        return BundleRecommendation.objects.create(product_a=self.own, product_b=self.second,
            sent_at=timezone.now(), is_current=True)

    def feed(self):
        return self.client.get(reverse('mobile_seller_recommendations'), {'source': 'admin'}, **self.auth)

    def action(self, row, action):
        return self.client.post(reverse('mobile_seller_recommendation_action'), json.dumps({
            'id': str(row.pk), 'source': 'admin', 'action': action}),
            content_type='application/json', **self.auth)

    def submit(self, row, key=None):
        data = {'name': 'Test admin bundle', 'price': '35.00', 'category': 'Snacks',
            'product_type': 'bundle', 'suggestion_source': 'admin', 'suggestion_id': str(row.pk),
            'bundle_components': [{'product_id': product.pk, 'required_quantity': 1, 'selections': []}
                                  for product in (self.own, self.second)]}
        if key is not None:
            data['submission_key'] = key
        return self.client.post(reverse('seller_submit_product'), json.dumps(data),
            content_type='application/json', **self.auth)

    def test_only_sent_owned_pairs_are_visible_and_get_never_mines_or_writes(self):
        row = BundleRecommendation.objects.create(product_a=self.own, product_b=self.second)
        before = AccountActivity.objects.count()
        with patch('modules.marketplace.services.bundle_suggestions.build_bundle_suggestions', side_effect=AssertionError):
            self.assertEqual(self.feed().json()['rows'], [])
            row.sent_at = timezone.now(); row.save()
            feed = self.feed().json()
        self.assertEqual(feed['rows'][0]['id'], str(row.pk))
        self.assertEqual(feed['rows'][0]['status'], 'pending')
        self.assertEqual(AccountActivity.objects.count(), before)

    def test_existing_admin_send_action_delivers_to_mobile_seller_feed(self):
        from django.contrib.auth.models import Permission
        from django.test import Client
        row = BundleRecommendation.objects.create(product_a=self.own, product_b=self.second)
        manager = User.objects.create_user(username='send-manager', role='Marketplace Admin',
            is_staff=True, department=self.program)
        manager.user_permissions.add(*Permission.objects.filter(content_type__app_label='accounts',
            codename__in=['can_view_marketplace_analytics', 'can_view_orders', 'can_manage_sellers']))
        admin = Client(); admin.force_login(manager)
        with patch('modules.marketplace.services.bundle_monitoring.build_bundle_suggestions', return_value={
                'error': False, 'source': 'live', 'rows': [{'products': [{'id': self.own.pk}, {'id': self.second.pk}]}]}):
            sent = admin.post(reverse('bundle_monitor_highlight', args=[row.pk]), HTTP_ACCEPT='application/json')
        self.assertEqual(sent.status_code, 200, sent.content)
        self.assertEqual(self.feed().json()['rows'][0]['id'], str(row.pk))

    def test_cross_owner_and_oversized_id_are_never_exposed_or_actionable(self):
        row = BundleRecommendation.objects.create(product_a=self.own, product_b=self.foreign, sent_at=timezone.now())
        self.assertEqual(self.feed().json()['rows'], [])
        self.assertEqual(self.action(row, 'accept').status_code, 404)
        response = self.client.post(reverse('mobile_seller_recommendation_action'),
            json.dumps({'id': '9' * 100, 'source': 'admin', 'action': 'accept'}),
            content_type='application/json', **self.auth)
        self.assertEqual(response.status_code, 404)

    def test_accept_persists_once_and_monitor_counts_response(self):
        row = self.sent()
        before = Product.objects.count()
        for _ in range(2):
            response = self.action(row, 'accept')
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()['status'], 'accepted')
        self.assertEqual(AccountActivity.objects.filter(metadata__decision='accepted').count(), 1)
        self.assertEqual(SellerBundleSuggestion.objects.get(seller=self.owner).state, 'saved')
        self.assertEqual(self.feed().json()['rows'][0]['status'], 'accepted')
        self.assertEqual(presentation(row)['response'], 'Accepted')
        root = User.objects.create_superuser(username='test-admin-root', password='test')
        self.assertEqual(activity_summary(root, include_rates=True)['rates']['responded'], 1)
        self.assertEqual(Product.objects.count(), before)

    def test_decline_is_persisted_visible_idempotent_and_final(self):
        row = self.sent()
        for _ in range(2):
            self.assertEqual(self.action(row, 'decline').status_code, 200)
        self.assertEqual(self.feed().json()['rows'][0]['status'], 'declined')
        self.assertFalse(self.feed().json()['rows'][0]['can_create'])
        self.assertEqual(presentation(row)['response'], 'Declined')
        self.assertEqual(AccountActivity.objects.filter(metadata__decision='declined').count(), 1)
        self.assertEqual(self.action(row, 'accept').status_code, 409)

    def test_foreign_unsent_and_anonymous_access_are_denied(self):
        row = BundleRecommendation.objects.create(product_a=self.own, product_b=self.second)
        self.assertEqual(self.action(row, 'accept').status_code, 404)
        row.sent_at = timezone.now(); row.save()
        from modules.messages.auth import mobile_chat_token
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + mobile_chat_token(self.other)}
        self.assertEqual(self.feed().json()['rows'], [])
        self.assertEqual(self.action(row, 'accept').status_code, 404)
        self.assertEqual(self.client.get(reverse('mobile_seller_recommendations'), {'source': 'admin'}).status_code, 401)

    def test_submit_requires_acceptance_then_creates_one_pending_owned_bundle(self):
        row = self.sent()
        self.assertEqual(self.submit(row).status_code, 400)
        self.assertEqual(self.action(row, 'accept').status_code, 200)
        before = (self.own.stock, self.second.stock)
        response = self.submit(row)
        self.assertEqual(response.status_code, 201, response.content)
        product = Product.objects.get(pk=response.json()['product']['id'])
        self.assertEqual(product.mobile_seller_id, self.owner.pk)
        self.assertEqual(product.approval_status, 'pending')
        self.assertEqual(product.source_recommendation_id, row.pk)
        self.assertEqual(product.bundle_components.count(), 2)
        self.assertEqual(self.feed().json()['rows'][0]['status'], 'bundle_created')
        self.assertEqual(self.submit(row).status_code, 400)
        self.own.refresh_from_db(); self.second.refresh_from_db()
        self.assertEqual((self.own.stock, self.second.stock), before)

    def test_legacy_saved_choice_is_not_fabricated_as_acceptance(self):
        self.sent()
        SellerBundleSuggestion.objects.create(seller=self.owner, product_a=self.own, product_b=self.second, state='saved')
        self.assertEqual(self.feed().json()['rows'][0]['status'], 'pending')

    def test_lost_response_retry_returns_same_product_without_duplicate_audit_or_inventory(self):
        row = self.sent()
        self.action(row, 'accept')
        first = self.submit(row, key='a' * 32)
        second = self.submit(row, key='a' * 32)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(first.json()['product']['id'], second.json()['product']['id'])
        self.assertEqual(Product.objects.filter(source_recommendation=row).count(), 1)
        self.assertEqual(AccountActivity.objects.filter(metadata__submission_key='a' * 32).count(), 1)

    def test_generic_saved_choice_removal_cannot_erase_admin_decision_history(self):
        row = self.sent()
        self.action(row, 'accept')
        SellerBundleSuggestion.objects.filter(seller=self.owner).delete()
        self.assertEqual(self.feed().json()['rows'][0]['status'], 'accepted')

    def test_decline_history_and_monitoring_survive_legacy_choice_removal(self):
        row = self.sent()
        self.action(row, 'decline')
        SellerBundleSuggestion.objects.filter(seller=self.owner).delete()
        self.assertEqual(self.feed().json()['rows'][0]['status'], 'declined')
        root = User.objects.create_superuser(username='decline-root', password='test')
        self.assertEqual(activity_summary(root)['summary']['dismissed'], 1)

    def test_suspension_archived_products_and_conflicting_decisions_are_rejected(self):
        row = self.sent()
        self.assertEqual(self.action(row, 'validate').status_code, 409)
        self.assertEqual(self.action(row, 'accept').status_code, 200)
        self.assertEqual(self.action(row, 'decline').status_code, 409)
        self.own.archive()
        self.assertEqual(self.action(row, 'validate').status_code, 409)
        self.assertEqual(self.submit(row).status_code, 400)
        self.application.is_suspended = True; self.application.save()
        self.assertEqual(self.feed().status_code, 403)

    def test_live_and_synthetic_actions_cannot_accept_or_submit_demo_as_real(self):
        row = self.sent()
        for source in ('live', 'synthetic'):
            response = self.client.post(reverse('mobile_seller_recommendation_action'),
                json.dumps({'id': str(row.pk), 'source': source, 'action': 'accept'}),
                content_type='application/json', **self.auth)
            self.assertEqual(response.status_code, 400)
