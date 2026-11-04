"""Flutter-wire-contract APIs, shared stock records and Admin Analytics in disposable PostgreSQL."""
from datetime import timedelta
import json
from uuid import uuid4
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from api.models import CampusHubUser, InventoryBatch, MarketplaceOrder, Product
from api import test_mobile_seller_workspace as mobile_seller_fixtures
from modules.messages.auth import mobile_chat_token
from modules.marketplace.services import fifo


@override_settings(CAMPUSHUB_FIFO_ENABLED=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class MarketplaceInventoryIntegrationTests(TestCase):
    account = mobile_seller_fixtures.MobileSellerWorkspaceTests.account
    product = mobile_seller_fixtures.MobileSellerWorkspaceTests.product

    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        mobile_seller_fixtures.MobileSellerWorkspaceTests.setUp(self)
        self.admin = User.objects.create_superuser(username='inventory-bridge-admin', role='Super Admin')
        self.admin_client = Client(); self.admin_client.force_login(self.admin)
        fifo.initialize(fifo.reconciliation()['fingerprint'])
        self.tracked = Product.objects.create(mobile_seller=self.owner, name='FIFO bridge item', price=20,
            stock=0, low_stock_threshold=3, inventory_method='fifo', category='Supplies', approval_status='approved')
        self.sku = self.tracked.inventory_skus.get(group_name='', variant_name='')
        self.buyer = self.account('inventory-bridge-buyer')
        self.buyer_auth = {'HTTP_AUTHORIZATION': 'Bearer ' + mobile_chat_token(self.buyer)}
        self.buyer_client = Client()

    def post_mobile(self, name, payload, *, buyer=False, **headers):
        return (self.buyer_client if buyer else self.client).post(reverse(name), json.dumps(payload),
            content_type='application/json', **(self.buyer_auth if buyer else self.auth), **headers)

    def receive(self):
        for quantity, days, reference in [(3, 3, 'Old receipt'), (4, 2, 'New receipt')]:
            payload = {'sku': self.sku.pk, 'quantity': quantity, 'reference': reference, 'key': str(uuid4()),
                       'received_at': (timezone.now() - timedelta(days=days)).isoformat()}
            response = self.post_mobile('mobile_seller_receive_stock', payload)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(self.post_mobile('mobile_seller_receive_stock', payload).json(), response.json())
        self.tracked.refresh_from_db()
        self.assertEqual(self.tracked.stock, 7)
        self.assertEqual(list(self.sku.batches.order_by('received_at').values_list('remaining_quantity', flat=True)), [3, 4])

    def analytics(self):
        response = self.admin_client.get(reverse('admin_marketplace_analytics_page'), {'period': '30'})
        self.assertEqual(response.status_code, 200)
        return response.context['analytics']

    def place(self, delivery=False):
        payload = {'product_id': self.tracked.pk, 'buyer_user_id': self.buyer.pk, 'quantity': 4, 'customization': [],
                   'expected_unit_price': '20.00', 'fulfillment_method': 'seller_delivery' if delivery else 'pickup',
                   'payment_method': 'cash_on_delivery' if delivery else 'cash_on_pickup'}
        if delivery:
            self.assertEqual(self.post_mobile('mobile_seller_delivery_setting', {'seller_delivery_enabled': True}).status_code, 200)
            payload['delivery_destination'] = 'Isolated campus test destination'
        key = str(uuid4())
        response = self.post_mobile('marketplace_orders', payload, buyer=True, HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(response.status_code, 201, response.content)
        replay = self.post_mobile('marketplace_orders', payload, buyer=True, HTTP_IDEMPOTENCY_KEY=key)
        self.assertIn(replay.status_code, (200, 201), replay.content)
        self.assertEqual(replay.json()['order']['id'], response.json()['order']['id'])
        return MarketplaceOrder.objects.get(pk=response.json()['order']['id'])

    def update(self, order, **payload):
        return self.admin_client.post(reverse('admin_order_update', args=[order.pk]), json.dumps(payload), content_type='application/json')

    def verify_hold(self, order):
        self.tracked.refresh_from_db()
        self.assertEqual(self.tracked.stock, 3)
        self.assertEqual(list(self.sku.batches.order_by('received_at').values_list('remaining_quantity', flat=True)), [0, 3])
        self.assertEqual(list(order.fifo_allocations.order_by('batch__received_at').values_list('quantity', flat=True)), [3, 1])
        workspace = self.client.get(reverse('mobile_seller_workspace'), **self.auth).json()
        row = next(row for row in workspace['inventory'] if row['product_id'] == self.tracked.pk)
        self.assertEqual((row['on_hand'], row['reserved'], row['available']), (7, 4, 3))
        data = self.analytics()
        self.assertEqual((data['operations']['total'], data['kpis']['sales']), (1, '0.00'))
        alert = next(row for row in data['stock_alerts'] if row['product'] == self.tracked.name)
        self.assertEqual((alert['available'], alert['threshold']), (3, 3))
        for tab in ('fifo', 'movements'):
            page = self.admin_client.get(reverse('admin_products_page'), {'view': 'inventory', 'inventory_section': tab})
            self.assertEqual(page.status_code, 200)

    def test_mobile_fifo_checkout_payment_completion_reconciles_analytics(self):
        self.receive(); order = self.place(); self.verify_hold(order)
        for action in ('start_processing', 'ready'):
            self.assertEqual(self.update(order, fulfillment_action=action).status_code, 200)
        for _ in range(2):
            self.assertEqual(self.update(order, status='completed', cash_confirmed=True, pickup_confirmed=True).status_code, 200)
        self.tracked.refresh_from_db(); order.refresh_from_db()
        self.assertEqual((self.tracked.stock, order.payment_status), (3, 'paid'))
        self.assertEqual(order.inventory_movements.filter(kind='sale').count(), 1)
        self.assertEqual(order.fifo_allocations.filter(state='consumed').count(), 2)
        data = self.analytics()
        self.assertEqual((data['kpis']['sales'], data['kpis']['completed_orders']), ('80.00', 1))
        self.assertEqual(data['top_products'][0]['units'], 4)
        self.assertEqual(data['seller_performance']['rows'][0]['seller_key'], f'mobile:{self.owner.pk}')
        self.assertEqual(data['operations']['fulfillment'][0]['count'], 1)

    def test_mobile_delivery_stays_unpaid_and_cancelled_hold_restores_once(self):
        self.receive(); order = self.place(delivery=True); self.verify_hold(order)
        for action in ('start_processing', 'ready', 'start_delivery', 'delivered'):
            self.assertEqual(self.update(order, fulfillment_action=action).status_code, 200)
        self.assertEqual(self.analytics()['kpis']['sales'], '0.00')
        self.assertEqual(self.update(order, status='cancelled', cancellation_reason='Isolated verification').status_code, 409)
        self.assertEqual(self.update(order, status='completed', cash_confirmed=True).status_code, 200)
        self.assertEqual(self.analytics()['kpis']['sales'], '80.00')
        # A fresh hold is cancelled before delivery; no completed stock is reversed.
        receipt = {'sku': self.sku.pk, 'quantity': 4, 'reference': 'Cancellation receipt', 'key': str(uuid4())}
        self.assertEqual(self.post_mobile('mobile_seller_receive_stock', receipt).status_code, 200)
        cancelled = self.place()
        for _ in range(2):
            self.assertEqual(self.update(cancelled, status='cancelled', cancellation_reason='Isolated cancellation').status_code, 200)
        self.tracked.refresh_from_db()
        self.assertEqual(self.tracked.stock, 7)
        self.assertEqual(cancelled.fifo_allocations.filter(state='released').count(), 2)
        self.assertEqual(cancelled.inventory_movements.filter(kind='release').count(), 1)
        self.assertEqual(self.analytics()['kpis']['sales'], '80.00')
        self.assertEqual(self.analytics()['operations']['total'], 2)
        self.assertEqual(self.analytics()['operations']['cancelled'], 1)
