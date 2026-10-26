"""Independent PostgreSQL connections exercise real row/unique-key contention."""
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
from unittest import skipUnless

from django.db import connection, close_old_connections, connections
from django.test import TransactionTestCase, Client, override_settings
from django.urls import reverse
from accounts.models import User
from api.models import Product, MarketplaceOrder, InventoryBatchAllocation
from .services import fifo


@skipUnless(connection.vendor == "postgresql", "FIFO contention requires PostgreSQL")
@override_settings(CAMPUSHUB_FIFO_ENABLED=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FIFOConcurrencyTests(TransactionTestCase):
    # Legacy unmanaged facility FKs require cascading cleanup in the TEST database.
    available_apps = ["accounts", "api", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions"]
    def setUp(self):
        self.admin = User.objects.create_superuser(username="fifo-race", role="Super Admin")
        self.product = Product.objects.create(seller=self.admin, name="Race item", stock=0, price=10, approval_status="approved")
        self.sku = self.product.inventory_skus.get(variant_name="")
        fifo.initialize(fifo.reconciliation()["fingerprint"])

    def race(self, action):
        barrier = Barrier(2)
        def work():
            close_old_connections()
            try:
                user = User.objects.get(pk=self.admin.pk)
                barrier.wait(timeout=10)
                return action(user)
            finally:
                connections["default"].close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(work) for _ in range(2)]
            return [future.result(timeout=30) for future in futures]

    def test_simultaneous_receipt_retry_posts_once(self):
        key = uuid4()
        results = self.race(lambda user: fifo.receive(self.sku.pk, 50, "Concurrent test receipt", user, key))
        self.assertEqual(results[0], results[1])
        self.product.refresh_from_db(); self.assertEqual(self.product.stock, 50)
        self.assertEqual(self.sku.batches.count(), 1)

    def request(self, quantity, key=None):
        client = Client()
        return client.post(reverse("marketplace_orders"), json.dumps({"product_id": self.product.pk,
            "quantity": quantity, "buyer_user_id": self.admin.pk}), content_type="application/json",
            **({"HTTP_IDEMPOTENCY_KEY": str(key)} if key else {})).status_code

    def test_simultaneous_orders_cannot_oversell(self):
        fifo.receive(self.sku.pk, 50, "Concurrent stock", self.admin, uuid4())
        self.assertEqual(sorted(self.race(lambda user: self.request(30))), [201, 409])
        self.product.refresh_from_db(); self.assertEqual(self.product.stock, 20)
        self.assertEqual(self.sku.batches.get().remaining_quantity, 20)
        self.assertEqual(MarketplaceOrder.objects.count(), 1)
        self.assertEqual(sum(InventoryBatchAllocation.objects.values_list("quantity", flat=True)), 30)

    def test_simultaneous_keyed_order_retry_allocates_once(self):
        fifo.receive(self.sku.pk, 50, "Retry stock", self.admin, uuid4())
        key = uuid4()
        self.assertEqual(self.race(lambda user: self.request(25, key)), [201, 201])
        self.assertEqual(MarketplaceOrder.objects.count(), 1)
        self.assertEqual(self.sku.batches.get().remaining_quantity, 25)

    def test_single_product_and_bundle_share_one_locked_pool(self):
        from itertools import count
        from api.models import BundleComponent
        fifo.receive(self.sku.pk, 50, "Shared race stock", self.admin, uuid4())
        bundle = Product.objects.create(seller=self.admin, name="Race bundle", price=15, stock=0, product_type="bundle", approval_status="approved")
        BundleComponent.objects.create(bundle=bundle, product=self.product, required_quantity=2)
        jobs = [(self.product.pk, 30), (bundle.pk, 15)]
        index = count()
        def buy(user):
            product_id, qty = jobs[next(index)]
            return Client().post(reverse("marketplace_orders"), json.dumps({"product_id":product_id,"quantity":qty,"buyer_user_id":user.pk}), content_type="application/json").status_code
        self.assertEqual(sorted(self.race(buy)), [201,409])
        self.product.refresh_from_db(); self.assertEqual(self.product.stock,20)
        self.assertEqual(self.sku.batches.get().remaining_quantity,20)
