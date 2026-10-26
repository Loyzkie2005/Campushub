"""Pickup/delivery semantics against isolated PostgreSQL records, never live stock."""
import json
import os
from pathlib import Path
from django.test import TestCase, override_settings
from django.urls import reverse
from django.db import connection
from api.models import CampusHubUser, MarketplaceOrder, SellerRequest
from accounts.models import Department
from modules.messages.auth import mobile_chat_token
from api import test_mobile_seller_workspace as seller_tests
from . import test_fifo_inventory as fifo_tests


@override_settings(CAMPUSHUB_FIFO_ENABLED=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class OrderFulfillmentTests(TestCase):
    setUp = fifo_tests.FIFOInventoryTests.setUp
    receive = fifo_tests.FIFOInventoryTests.receive
    cancel = fifo_tests.FIFOInventoryTests.cancel

    def place(self, **extra):
        payload = {"product_id":self.product.pk, "buyer_user_id":self.admin.pk,
            "quantity":2, "fulfillment_method":"seller_delivery", "delivery_destination":"Actual isolated test destination"}
        payload.update(extra)
        return self.client.post(reverse("marketplace_orders"), json.dumps(payload), content_type="application/json")

    def update(self, order, **data):
        return self.client.post(reverse("admin_order_update", args=[order.pk]), json.dumps(data), content_type="application/json")

    def advance(self, order, action):
        return self.update(order, fulfillment_action=action)

    def export(self, name):
        if os.environ.get("ORDERS_REVIEW_DIR"):
            (Path(os.environ["ORDERS_REVIEW_DIR"])/(name+".html")).write_bytes(self.client.get(reverse("admin_orders_page")).content)

    def order(self, qty, *, product=None, selections=None, key=None):
        headers={"HTTP_IDEMPOTENCY_KEY":str(key)} if key else {}
        return self.client.post(reverse("marketplace_orders"),json.dumps({"product_id":(product or self.product).pk,
            "buyer_user_id":self.admin.pk,"quantity":qty,"customization":selections or [],
            "fulfillment_method":"seller_delivery","delivery_destination":"Actual isolated destination"}),content_type="application/json",**headers)

    def test_seller_delivery_variants_keep_stable_skus_and_original_cancellation(self):
        fifo_tests.FIFOInventoryTests.test_variant_batches_use_stable_skus_and_survive_reordering(self)

    def test_seller_delivery_bundles_keep_recorded_component_recipe(self):
        fifo_tests.FIFOInventoryTests.test_bundle_components_and_changed_recipe_restore_recorded_batches(self)

    def test_delivery_reservation_stays_open_unpaid_until_explicit_paid_completion(self):
        self.receive(1); self.receive(4)
        response=self.place();self.assertEqual(response.status_code,201,response.content)
        order=MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(list(order.fifo_allocations.order_by("batch_id").values_list("quantity", flat=True)),[1,1])
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True,pickup_confirmed=True).status_code,409)
        for action in ("start_processing","ready"):
            self.assertEqual(self.advance(order,action).status_code,200)
        self.export("delivery-ready")
        self.assertEqual(self.advance(order,"delivered").status_code,409)
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True,pickup_confirmed=True).status_code,409)
        for action in ("start_delivery","delivered","delivered"):
            self.assertEqual(self.advance(order,action).status_code,200)
            if action=="start_delivery": self.export("delivery-outbound")
        self.export("delivery-waiting")
        order.refresh_from_db(); self.product.refresh_from_db()
        self.assertEqual((order.status,order.payment_status,self.product.stock),("ready_for_pickup","unpaid",3))
        self.assertIsNotNone(order.delivered_at);self.assertIsNone(order.completed_at);self.assertIsNone(order.picked_up_at)
        self.assertEqual(order.fifo_allocations.filter(state="reserved").count(),2)
        self.assertEqual(order.status_history.filter(notes__startswith="Seller delivery confirmed").count(),1)
        from .services.analytics import valid_sales_queryset
        self.assertFalse(valid_sales_queryset().filter(pk=order.pk).exists())
        self.assertEqual(self.cancel(order).status_code,409)
        self.assertEqual(self.update(order,status="completed").status_code,409)
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True).status_code,200)
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True).status_code,200)
        self.export("delivery-completed")
        order.refresh_from_db();self.product.refresh_from_db()
        self.assertEqual((order.status,order.payment_status,self.product.stock),("completed","paid",3))
        self.assertIsNone(order.picked_up_at)
        self.assertEqual(order.fifo_allocations.filter(state="consumed").count(),2)
        self.assertTrue(valid_sales_queryset().filter(pk=order.pk).exists())
        self.assertEqual(order.inventory_movements.filter(kind="sale").count(),1)
        self.assertEqual(self.update(order,payment_status="unpaid").status_code,409)

    def test_cancel_before_delivery_restores_original_batches_once(self):
        self.receive(1);self.receive(4)
        order=MarketplaceOrder.objects.get(pk=self.place().json()["order"]["id"])
        for action in ("start_processing","ready","start_delivery"): self.assertEqual(self.advance(order,action).status_code,200)
        self.assertEqual(self.cancel(order).status_code,200);self.assertEqual(self.cancel(order).status_code,200)
        self.assertEqual(list(self.sku.batches.order_by("pk").values_list("remaining_quantity",flat=True)),[1,4])
        self.assertEqual(self.advance(order,"delivered").status_code,409)

    def test_pickup_completion_and_legacy_values_remain_separate(self):
        self.receive(10)
        order=MarketplaceOrder.objects.get(pk=self.place(fulfillment_method="pickup",delivery_destination="").json()["order"]["id"])
        self.assertEqual(self.advance(order,"start_processing").status_code,200)
        self.assertEqual(self.advance(order,"ready").status_code,200)
        self.assertEqual(self.advance(order,"start_delivery").status_code,409)
        self.assertEqual(self.update(order,status="completed").status_code,409)
        self.assertEqual(self.update(order,status="completed",cash_confirmed=True,pickup_confirmed=True).status_code,200)
        order.refresh_from_db();self.assertIsNotNone(order.picked_up_at);self.assertIsNone(order.delivered_at)
        legacy=MarketplaceOrder.objects.create(product_name="Actual isolated legacy record")
        self.assertEqual(legacy.fulfillment_method,"");self.assertIsNone(legacy.delivered_at)

    def test_idempotent_delivery_creation_still_authorizes_before_cached_replay(self):
        from uuid import uuid4
        self.receive(4)
        key=str(uuid4());payload={"product_id":self.product.pk,"buyer_user_id":self.admin.pk,"quantity":1,
            "fulfillment_method":"seller_delivery","delivery_destination":"Actual isolated destination"}
        url=reverse("marketplace_orders")
        for _ in range(2):
            response=self.client.post(url,json.dumps(payload),content_type="application/json",HTTP_IDEMPOTENCY_KEY=key)
            self.assertEqual(response.status_code,201)
        self.assertEqual(MarketplaceOrder.objects.count(),1)
        self.product.refresh_from_db();self.assertEqual(self.product.stock,3)
        self.client.logout()
        response=self.client.post(url,json.dumps(payload),content_type="application/json",HTTP_IDEMPOTENCY_KEY=key)
        self.assertEqual(response.status_code,401)

    def test_invalid_fulfillment_is_rejected_before_stock_write_and_buyer_is_bound(self):
        self.receive(10)
        for fields in ({"delivery_destination":""},{"fulfillment_method":"courier"},
                       {"fulfillment_method":"pickup"},{"delivery_destination":"x"*501},
                       {"fulfillment_method":[]},{"buyer_user_id":999999}):
            self.assertIn(self.place(**fields).status_code,(400,403))
        self.product.refresh_from_db();self.assertEqual(self.product.stock,10)
        self.assertEqual(MarketplaceOrder.objects.count(),0)
        self.client.logout();self.assertEqual(self.place().status_code,401)
        self.assertEqual(self.client.get(reverse("marketplace_orders")).status_code,401)

    def test_fulfillment_filter_labels_kpi_and_responsive_fixture(self):
        self.receive(12)
        responses=[self.place(),self.place(fulfillment_method="pickup",delivery_destination="")]
        orders=[MarketplaceOrder.objects.get(pk=r.json()["order"]["id"]) for r in responses]
        for order in orders:
            for action in ("start_processing","ready"): self.assertEqual(self.advance(order,action).status_code,200)
        for action in ("start_delivery","delivered"):self.assertEqual(self.advance(orders[0],action).status_code,200)
        url=reverse("admin_orders_page")
        page=self.client.get(url);self.assertEqual(page.context["order_stats"]["ready_for_pickup"],1)
        MarketplaceOrder.objects.create(product_name="Actual isolated unknown fulfillment",status="ready_for_pickup")
        self.assertEqual(self.client.get(url).context["order_stats"]["ready_for_pickup"],1)
        self.assertContains(page,"Ready for Seller Delivery");self.assertContains(page,"Delivered")
        self.assertContains(page,'class="col-fulfillment"')
        filtered=self.client.get(url,{"fulfillment":"seller_delivery","status":"ready_for_pickup","payment":"unpaid","search":"FIFO"})
        self.assertEqual([o.pk for o in filtered.context["orders"]],[orders[0].pk])
        self.assertFalse(self.client.get(url,{"fulfillment":"courier"}).context["orders"])
        if os.environ.get("ORDERS_REVIEW_DIR"):
            directory=Path(os.environ["ORDERS_REVIEW_DIR"])
            (directory/"delivery.html").write_bytes(page.content)
            (directory/"delivery-filtered.html").write_bytes(filtered.content)


@override_settings(CAMPUSHUB_FIFO_ENABLED=False)
class SellerDeliveryAccessTests(TestCase):
    account=seller_tests.MobileSellerWorkspaceTests.account
    product=seller_tests.MobileSellerWorkspaceTests.product
    order=seller_tests.MobileSellerWorkspaceTests.order

    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor: editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        self.program,_=Department.objects.get_or_create(code="BSIT",defaults={"name":"Information Technology","is_program":True})
        self.owner=self.account("delivery-owner");self.other=self.account("delivery-other")
        self.application=SellerRequest.objects.create(mobile_user=self.owner,status="approved")
        SellerRequest.objects.create(mobile_user=self.other,status="approved")
        self.auth={"HTTP_AUTHORIZATION":"Bearer "+mobile_chat_token(self.owner)}
        self.own=self.product(self.owner,"Owned delivery")
        self.foreign=self.product(self.other,"Foreign delivery")
        self.owned_order=self.order(self.own,status="pending",payment_status="unpaid",completed_at=None,fulfillment_method="seller_delivery",delivery_destination="Actual isolated destination")

    def post(self,order=None,auth=None,**data):
        return self.client.post(reverse("mobile_seller_order_progress",args=[(order or self.owned_order).pk]),json.dumps(data),content_type="application/json",**(self.auth if auth is None else auth))

    def test_only_approved_active_owner_can_progress_and_cannot_record_payment(self):
        foreign=self.order(self.foreign,status="pending",payment_status="unpaid",fulfillment_method="seller_delivery")
        self.assertEqual(self.post(auth={},action="start_processing").status_code,401)
        self.assertEqual(self.post(foreign,action="start_processing").status_code,404)
        self.assertEqual(self.post(action="delivered").status_code,409)
        self.assertEqual(self.post(action="ready",payment_status="paid").status_code,400)
        for action in ("start_processing","ready","start_delivery","delivered"):
            self.assertEqual(self.post(action=action).status_code,200)
        self.owned_order.refresh_from_db();self.assertEqual(self.owned_order.payment_status,"unpaid")
        self.assertIsNone(self.owned_order.completed_at)
        self.assertEqual(self.owned_order.status,"ready_for_pickup")
        self.assertEqual(self.post(action="completed").status_code,400)
        self.assertEqual(self.post(action=[]).status_code,400)
        SellerRequest.objects.filter(pk=self.application.pk).update(is_suspended=True)
        self.assertEqual(self.post(action="delivered").status_code,403)
        self.assertEqual(self.client.get(reverse("marketplace_orders"),{"user_id":self.other.pk},**self.auth).json()["orders"],[])

