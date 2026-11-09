# Original location: backend/core/modules/marketplace/test_product_ownership.py
"""Real authenticated owner/buyer requests in disposable PostgreSQL only."""
import json
from unittest.mock import patch
from uuid import uuid4
from django.test import TestCase, override_settings
from django.urls import reverse
from django.db import connection
from accounts.models import User
from api.models import (CampusHubUser, Product, MarketplaceOrder, ProductInteraction,
                        InventoryOperation, InventoryStockMovement)
from api.tests import test_mobile_seller_workspace as fixtures
from modules.messages.auth import mobile_chat_token
from modules.marketplace.services.product_ownership import owns_product


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ProductOwnershipTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()
    setUp = fixtures.MobileSellerWorkspaceTests.setUp
    account = fixtures.MobileSellerWorkspaceTests.account
    product = fixtures.MobileSellerWorkspaceTests.product

    def post(self, route, payload, actor=None, **headers):
        actor = actor or self.owner
        return self.client.post(reverse(route), json.dumps(payload), content_type='application/json',
            HTTP_AUTHORIZATION='Bearer ' + mobile_chat_token(actor), **headers)

    def test_self_orders_quotes_and_all_buyer_intents_are_denied_without_writes(self):
        before = (MarketplaceOrder.objects.count(), InventoryOperation.objects.count(),
                  InventoryStockMovement.objects.count(), ProductInteraction.objects.count())
        for method in ('', 'pickup'):
            payload = {'buyer_user_id': self.owner.pk, 'product_id': self.own.pk, 'quantity': 1}
            if method: payload['fulfillment_method'] = method
            response = self.post('marketplace_orders', payload, HTTP_IDEMPOTENCY_KEY=str(uuid4()))
            self.assertEqual(response.status_code, 403, response.content)
        self.assertEqual(self.post('marketplace_checkout_quote', {'items': [
            {'product_id': self.foreign.pk, 'quantity': 1},
            {'product_id': self.own.pk, 'quantity': 1}]}).status_code, 403)
        for intent in ('cart', 'favorite', 'chat'):
            self.assertEqual(self.post('track_product_interaction', {
                'user_id': self.owner.pk, 'product_id': self.own.pk, 'intent': intent}).status_code, 403)
        self.assertEqual(self.post('track_product_interaction', {
            'user_id': self.owner.pk, 'product_id': self.own.pk,
            'interaction_type': 'purchase'}).status_code, 403)
        self.own.refresh_from_db()
        self.assertEqual(self.own.stock, 10)
        self.assertEqual(before, (MarketplaceOrder.objects.count(), InventoryOperation.objects.count(),
                         InventoryStockMovement.objects.count(), ProductInteraction.objects.count()))

    def test_seller_can_buy_another_seller_product_and_read_own_product(self):
        for intent in ('cart', 'favorite', 'chat'):
            response = self.post('track_product_interaction', {'user_id': self.owner.pk,
                'product_id': self.foreign.pk, 'intent': intent})
            self.assertEqual(response.status_code, 200, response.content)
            self.assertTrue(response.json()['allowed'])
        self.assertFalse(ProductInteraction.objects.exists())
        response = self.post('track_product_interaction', {'user_id': self.owner.pk,
            'product_id': self.own.pk, 'interaction_type': 'view'})
        self.assertEqual(response.status_code, 201)
        quote = self.post('marketplace_checkout_quote', {'items': [{'product_id': self.foreign.pk, 'quantity': 1}]})
        self.assertEqual(quote.status_code, 200, quote.content)
        response = self.post('marketplace_orders', {'buyer_user_id': self.owner.pk,
            'product_id': self.foreign.pk, 'quantity': 1, 'fulfillment_method': 'pickup'})
        self.assertEqual(response.status_code, 201, response.content)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.stock, 9)

    def test_forged_identity_missing_auth_and_legacy_order_fields_cannot_bypass(self):
        for route, payload in (
            ('marketplace_orders', {'buyer_user_id': self.other.pk, 'product_id': self.own.pk, 'quantity': 1}),
            ('track_product_interaction', {'user_id': self.other.pk, 'product_id': self.own.pk, 'intent': 'cart'}),
        ):
            self.assertEqual(self.post(route, payload).status_code, 403)
            self.assertEqual(self.client.post(reverse(route), json.dumps(payload), content_type='application/json').status_code, 401)
        self.assertFalse(MarketplaceOrder.objects.exists())

    def test_admin_and_mobile_numeric_ids_are_distinct_and_session_owner_is_denied(self):
        admin = User.objects.create_user(pk=self.owner.pk, username='same-numeric-owner', role='Student')
        admin_product = Product.objects.create(seller=admin, name='Admin product', price=10, stock=10,
                                              approval_status='approved')
        self.assertFalse(owns_product(self.owner, admin_product))
        self.assertFalse(owns_product(admin, self.own))
        self.assertTrue(owns_product(admin, admin_product))
        self.assertEqual(self.post('marketplace_checkout_quote', {'items': [
            {'product_id': admin_product.pk, 'quantity': 1}]}).status_code, 200)
        self.client.force_login(admin)
        response = self.client.post(reverse('marketplace_orders'), json.dumps({
            'product_id': admin_product.pk, 'buyer_user_id': admin.pk, 'quantity': 1}), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_ownership_is_rechecked_under_product_lock(self):
        # Simulate ownership changing between the outer guard and locked write.
        from modules.marketplace.services import product_ownership
        with patch.object(product_ownership, 'owns_product', side_effect=[False, True]):
            response = self.post('marketplace_orders', {'buyer_user_id': self.owner.pk,
                'product_id': self.own.pk, 'quantity': 1})
        self.assertEqual(response.status_code, 403, response.content)
        self.assertFalse(MarketplaceOrder.objects.exists())

    def test_inactive_and_invalid_token_cannot_authorize_interaction(self):
        payload = {'user_id': self.owner.pk, 'product_id': self.foreign.pk, 'intent': 'cart'}
        self.owner.is_suspended = True
        self.owner.save(update_fields=['is_suspended'])
        self.assertEqual(self.post('track_product_interaction', payload).status_code, 403)
        response = self.client.post(reverse('track_product_interaction'), json.dumps(payload),
            content_type='application/json', HTTP_AUTHORIZATION='Bearer invalid')
        self.assertEqual(response.status_code, 401)

    def test_malformed_product_and_intent_cannot_crash_or_authorize_a_write(self):
        payload = {'user_id': self.owner.pk, 'product_id': self.foreign.pk, 'intent': 'cart'}
        for extra in ({'product_id': []}, {'product_id': True}, {'product_id': 'invalid'},
                      {'intent': []}, {'interaction_type': []}):
            response = self.post('track_product_interaction', {**payload, **extra})
            self.assertEqual(response.status_code, 400, response.content)
        self.assertFalse(ProductInteraction.objects.exists())
