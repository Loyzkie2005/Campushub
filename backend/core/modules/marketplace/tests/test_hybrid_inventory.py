# Original location: backend/core/modules/marketplace/test_hybrid_inventory.py
"""Hybrid workflows against disposable real PostgreSQL; no working-data seeds."""
import json
from uuid import uuid4
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import User, Department
from api.models import Product, MarketplaceOrder, BundleComponent, InventoryBatch, InventoryStockMovement, InventoryFIFOControl
from modules.marketplace.services import fifo
from modules.marketplace.services.inventory import get_product_inventory_snapshot
from modules.marketplace.tests import test_fifo_inventory as fifo_tests


@override_settings(CAMPUSHUB_FIFO_ENABLED=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class HybridInventoryTests(TestCase):
    order = fifo_tests.FIFOInventoryTests.order
    cancel = fifo_tests.FIFOInventoryTests.cancel

    def setUp(self):
        self.program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name":"Information Technology", "is_program":True})
        self.admin = User.objects.create_superuser(username="hybrid-admin", department=self.program, role="Super Admin")
        self.product = Product.objects.create(seller=self.admin, name="Secondhand uniform", price=10, stock=1, category="Clothing", approval_status="approved", low_stock_threshold=0)
        self.sku = self.product.inventory_skus.get(variant_name="")
        fifo.initialize(fifo.reconciliation()["fingerprint"])
        self.client.force_login(self.admin)

    def test_simple_is_default_and_activation_creates_no_batches_or_quantity_changes(self):
        self.product.refresh_from_db()
        self.assertEqual((self.product.inventory_method,self.product.stock), ("simple",1))
        self.assertFalse(InventoryBatch.objects.exists())
        self.assertEqual(self.sku.movements.get().quantity_change,1)

    def test_simple_receipt_retries_without_batches_even_when_fifo_engine_disabled(self):
        key=uuid4()
        with override_settings(CAMPUSHUB_FIFO_ENABLED=False):
            first=fifo.receive(self.sku.pk,3,"Real simple receipt",self.admin,key,notes="Received three uniforms")
            self.assertEqual(fifo.receive(self.sku.pk,3,"Real simple receipt",self.admin,key,notes="Received three uniforms"),first)
        self.assertIsNone(first["batch"])
        self.product.refresh_from_db();self.assertEqual(self.product.stock,4)
        self.assertFalse(InventoryBatch.objects.exists())
        movement=self.sku.movements.get(kind="receipt")
        self.assertEqual((movement.available_before,movement.available_after,movement.balance),(1,4,"on_hand"))
        self.assertEqual(movement.reference,"Real simple receipt")
        self.assertIsNotNone(movement.received_at)

    def test_simple_reservation_completion_and_keyed_retry_change_physical_stock_once(self):
        key=uuid4();response=self.order(1,key=key)
        self.assertEqual(response.status_code,201,response.content)
        self.assertEqual(self.order(1,key=key).json(),response.json())
        self.product.refresh_from_db()
        snapshot=get_product_inventory_snapshot(self.product)
        self.assertEqual((snapshot["on_hand"],snapshot["reserved"],snapshot["available"]),(1,1,0))
        order=MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        for status in ("processing","ready_for_pickup","completed","completed"):
            result=self.client.post(reverse("admin_order_update",args=[order.pk]),json.dumps({"status":status,"payment_status":"paid","pickup_confirmed":True}),content_type="application/json")
            self.assertEqual(result.status_code,200,result.content)
        sale=order.inventory_movements.get(kind="sale")
        self.assertEqual((sale.available_before,sale.available_after),(1,0))
        self.product.refresh_from_db();self.assertEqual(self.product.stock,0)
        self.assertFalse(InventoryBatch.objects.exists())

    def test_simple_cancellation_releases_hold_and_shortage_has_no_partial_write(self):
        response=self.order(1);self.assertEqual(response.status_code,201)
        self.assertEqual(self.order(1).status_code,409)
        order=MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(self.cancel(order).status_code,200)
        self.assertEqual(self.cancel(order).status_code,200)
        self.product.refresh_from_db();self.assertEqual(self.product.stock,1)
        self.assertEqual(order.inventory_movements.filter(kind="release").count(),1)

    def test_receiving_simple_with_live_hold_records_physical_balances(self):
        self.assertEqual(self.order(1).status_code,201)
        fifo.receive(self.sku.pk,2,"",self.admin,uuid4())
        movement=self.sku.movements.get(kind="receipt")
        self.assertEqual((movement.available_before,movement.available_after),(1,3))
        self.product.refresh_from_db();snapshot=get_product_inventory_snapshot(self.product)
        self.assertEqual((snapshot["on_hand"],snapshot["reserved"],snapshot["available"]),(3,1,2))

    def test_explicit_fifo_transition_preserves_current_available_and_original_hold(self):
        response=self.order(1);order=MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        fifo.receive(self.sku.pk,3,"New batch",self.admin,uuid4(),inventory_method="fifo")
        batches=list(self.sku.batches.order_by("pk"))
        self.assertEqual([(b.origin,b.initial_quantity,b.remaining_quantity) for b in batches],[("opening",1,0),("receipt",3,3)])
        self.assertIsNone(batches[0].received_at)
        self.assertTrue(order.fifo_allocations.get().legacy)
        self.assertEqual(self.cancel(order).status_code,200)
        self.product.refresh_from_db();self.assertEqual(self.product.stock,4)
        self.assertEqual(sum(self.sku.batches.values_list("remaining_quantity",flat=True)),4)

    def test_fifo_cannot_be_silently_downgraded_with_live_stock(self):
        self.product.inventory_method="fifo";self.product.save(update_fields=["inventory_method"])
        self.product.inventory_method="simple"
        with self.assertRaises(fifo.FIFOError):self.product.save(update_fields=["inventory_method"])
        self.product.refresh_from_db();self.assertEqual(self.product.inventory_method,"fifo")

    def test_mixed_bundle_reserves_and_completes_each_component_once(self):
        tracked=Product.objects.create(seller=self.admin,name="Batch component",price=2,stock=0,approval_status="approved",inventory_method="fifo")
        sku=tracked.inventory_skus.get(variant_name="")
        fifo.receive(sku.pk,2,"First batch",self.admin,uuid4());fifo.receive(sku.pk,3,"Second batch",self.admin,uuid4())
        bundle=Product.objects.create(seller=self.admin,name="Mixed bundle",price=10,product_type="bundle",stock=0,approval_status="approved")
        BundleComponent.objects.create(bundle=bundle,product=self.product,required_quantity=1)
        BundleComponent.objects.create(bundle=bundle,product=tracked,required_quantity=3)
        response=self.order(1,product=bundle);self.assertEqual(response.status_code,201,response.content)
        order=MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(list(order.fifo_allocations.order_by("batch_id").values_list("quantity",flat=True)),[2,1])
        self.assertFalse(self.sku.batches.exists());self.assertFalse(bundle.inventory_skus.get().batches.exists())
        for status in ("processing","ready_for_pickup","completed","completed"):
            result=self.client.post(reverse("admin_order_update",args=[order.pk]),json.dumps({"status":status,"payment_status":"paid","pickup_confirmed":True}),content_type="application/json")
            self.assertEqual(result.status_code,200,result.content)
        sales={row.sku.product_id:(row.available_before,row.available_after) for row in order.inventory_movements.filter(kind="sale").select_related("sku")}
        self.assertEqual(sales,{self.product.pk:(1,0),tracked.pk:(5,2)})
        self.product.refresh_from_db();tracked.refresh_from_db();self.assertEqual((self.product.stock,tracked.stock),(0,2))

    def test_global_history_and_product_history_use_same_persisted_receipt(self):
        fifo.receive(self.sku.pk,2,"Simple receipt search",self.admin,uuid4(),notes="Audit note")
        page=self.client.get(reverse("admin_products_page"),{"view":"inventory","inventory_section":"movements","search":"Simple receipt search"})
        self.assertEqual(len(page.context["fifo_movements"]),1)
        detail=self.client.get(reverse("admin_products_page"),{"view":"inventory","inventory_item":self.sku.pk})
        history=detail.context["inventory_detail"]["movements"]
        self.assertEqual(history[0]["reference"],"Simple receipt search")
        self.assertEqual(history[0]["notes"],"Audit note")

    def test_simple_empty_batches_is_not_a_configuration_error(self):
        with override_settings(CAMPUSHUB_FIFO_ENABLED=False):
            page=self.client.get(reverse("admin_products_page"),{"view":"inventory","inventory_section":"fifo"})
        self.assertContains(page,"No stock batches recorded yet.")
        self.assertContains(page,'id="fifoReceiveForm"')
        self.assertNotContains(page,"Stock receiving is not configured.")

    def test_simple_variant_receipts_never_combine_pools(self):
        product=Product.objects.create(seller=self.admin,name="Sizes",price=1,stock=3,approval_status="approved",customization_enabled=True,
            customization_options=[{"name":"Size","selection":"single","options":[{"name":"S","stock":1},{"name":"L","stock":2}]}])
        small=product.inventory_skus.get(variant_name="S")
        fifo.receive(small.pk,4,"Small uniforms",self.admin,uuid4())
        product.refresh_from_db()
        self.assertEqual([option["stock"] for option in product.customization_options[0]["options"]],[5,2])
        self.assertFalse(InventoryBatch.objects.exists())

    def test_mixed_bundle_shortage_leaves_all_components_unchanged(self):
        tracked=Product.objects.create(seller=self.admin,name="Short component",price=2,stock=1,approval_status="approved",inventory_method="fifo")
        bundle=Product.objects.create(seller=self.admin,name="Short bundle",price=10,product_type="bundle",stock=0,approval_status="approved")
        BundleComponent.objects.create(bundle=bundle,product=self.product,required_quantity=1)
        BundleComponent.objects.create(bundle=bundle,product=tracked,required_quantity=2)
        before=InventoryStockMovement.objects.count()
        self.assertEqual(self.order(1,product=bundle).status_code,409)
        self.product.refresh_from_db();tracked.refresh_from_db()
        self.assertEqual((self.product.stock,tracked.stock),(1,1))
        self.assertEqual(InventoryStockMovement.objects.count(),before)
        self.assertFalse(MarketplaceOrder.objects.exists())
