# Original location: backend/core/modules/marketplace/test_checkout.py
"""Checkout integration writes only isolated test PostgreSQL records."""
import json
from uuid import uuid4
from django.test import TestCase
from django.db import connection
from django.urls import reverse
from api.models import MarketplaceOrder, SellerRequest, CampusHubUser, BundleComponent
from api.tests import test_mobile_seller_workspace as seller_tests


class CheckoutTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()
    account = seller_tests.MobileSellerWorkspaceTests.account
    product = seller_tests.MobileSellerWorkspaceTests.product
    setUp = seller_tests.MobileSellerWorkspaceTests.setUp

    def post(self, name, data, auth=None, **headers):
        from modules.messages.auth import mobile_chat_token
        default_auth = ({'HTTP_AUTHORIZATION': 'Bearer ' + mobile_chat_token(self.other)}
                        if name in {'marketplace_orders', 'marketplace_checkout_quote'} else self.auth)
        return self.client.post(reverse(name), json.dumps(data), content_type="application/json",
                                **(default_auth if auth is None else auth), **headers)

    def item(self, **extra):
        return {"product_id": self.own.pk, "quantity": 2, "customization": [], **extra}

    def place(self, **extra):
        return self.post("marketplace_orders", {**self.item(), "buyer_user_id": self.other.pk,
            "fulfillment_method": "pickup", "payment_method": "cash_on_pickup",
            "expected_unit_price": "20.00", **extra})

    def test_default_disabled_quote_reads_real_prices_and_never_reserves(self):
        quote = self.post("marketplace_checkout_quote", {"items": [self.item()]})
        self.assertEqual(quote.status_code, 200, quote.content)
        self.assertEqual(quote.json()["items"][0], {"product_id": self.own.pk, "quantity": 2,
            "available": 10, "unit_price": "20.00", "subtotal": "40.00", "total": "40.00",
            "delivery_fee": "0.00", "delivery_supported": False})
        self.own.refresh_from_db(); self.assertEqual(self.own.stock, 10)
        self.assertFalse(MarketplaceOrder.objects.exists())

    def test_only_active_approved_seller_can_update_own_setting(self):
        url = "mobile_seller_delivery_setting"
        self.assertIn(self.post(url, {"seller_delivery_enabled": True}, auth={}).status_code, (401, 403))
        for data in ({"seller_delivery_enabled": "true"}, {"seller_delivery_enabled": True, "seller_id": self.other.pk}):
            self.assertEqual(self.post(url, data).status_code, 400)
        self.assertEqual(self.post(url, {"seller_delivery_enabled": True}).json(), {"seller_delivery_enabled": True})
        self.application.refresh_from_db(); self.assertTrue(self.application.seller_delivery_enabled)
        self.assertFalse(SellerRequest.objects.get(mobile_user=self.other).seller_delivery_enabled)
        self.application.is_suspended = True; self.application.save()
        self.assertEqual(self.post(url, {"seller_delivery_enabled": False}).status_code, 403)

    def test_toggle_controls_quote_and_disabled_delivery_cannot_be_forged(self):
        self.assertEqual(self.place(fulfillment_method="seller_delivery", payment_method="cash_on_delivery",
            delivery_destination="Library entrance").status_code, 400)
        self.post("mobile_seller_delivery_setting", {"seller_delivery_enabled": True})
        quote = self.post("marketplace_checkout_quote", {"items": [self.item()]}).json()["items"][0]
        self.assertTrue(quote["delivery_supported"])
        response = self.place(fulfillment_method="seller_delivery", payment_method="cash_on_delivery", delivery_destination="Library entrance")
        self.assertEqual(response.status_code, 201, response.content)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual((order.fulfillment_method, order.delivery_destination, order.payment_status, order.total_price),
                         ("seller_delivery", "Library entrance", "unpaid", 40))
        self.assertEqual(response.json()["order"]["payment_method_label"], "Cash on Delivery")
        self.assertEqual(response.json()["order"]["fulfillment_label"], "Seller Delivery")
        workspace = self.client.get(self.url, **self.auth).json()
        self.assertTrue(workspace["seller"]["seller_delivery_enabled"])
        self.assertEqual(workspace["orders"][0]["id"], order.pk)
        self.post("mobile_seller_delivery_setting", {"seller_delivery_enabled": False})
        order.refresh_from_db(); self.assertEqual(order.fulfillment_method, "seller_delivery")
        self.assertEqual(self.place(fulfillment_method="seller_delivery", payment_method="cash_on_delivery", delivery_destination="Library entrance").status_code, 400)

    def test_pickup_needs_no_location_and_cash_is_unpaid(self):
        response = self.place()
        self.assertEqual(response.status_code, 201, response.content)
        row = response.json()["order"]
        self.assertEqual((row["fulfillment_label"], row["payment_method_label"], row["delivery_destination"], row["payment_status"]),
                         ("Customer Pickup", "Cash on Pickup", "", "unpaid"))

    def test_invalid_location_mapping_quantity_and_changed_price_leave_stock_intact(self):
        self.post("mobile_seller_delivery_setting", {"seller_delivery_enabled": True})
        for location in ("", "    ", "....!", "a", "x" * 501):
            self.assertEqual(self.place(fulfillment_method="seller_delivery", payment_method="cash_on_delivery", delivery_destination=location).status_code, 400)
        for quantity in (0, -1, True, 1.5, "bad"):
            self.assertEqual(self.place(quantity=quantity).status_code, 400)
        self.assertEqual(self.place(payment_method="cash_on_delivery").status_code, 400)
        self.assertEqual(self.place(expected_unit_price="19.00").status_code, 409)
        self.own.refresh_from_db(); self.assertEqual(self.own.stock, 10)
        self.assertFalse(MarketplaceOrder.objects.exists())

    def test_quote_rejects_missing_products_overselling_and_unauthenticated_requests(self):
        self.assertEqual(self.post("marketplace_checkout_quote", {"items": [self.item()]}, auth={}).status_code, 401)
        for item in (self.item(quantity=11), self.item(product_id=999999), self.item(quantity=0)):
            self.assertEqual(self.post("marketplace_checkout_quote", {"items": [item]}).status_code, 400)
        shared = self.post("marketplace_checkout_quote", {"items": [self.item(quantity=6), self.item(quantity=6)]})
        self.assertEqual(shared.status_code, 400)
        self.assertIn("share insufficient stock", shared.json()["error"])

    def test_repeat_submission_creates_once_and_history_without_method_stays_unknown(self):
        payload = {**self.item(), "buyer_user_id": self.other.pk, "fulfillment_method": "pickup", "payment_method": "cash_on_pickup", "expected_unit_price": "20.00"}
        key = str(uuid4())
        responses = [self.post("marketplace_orders", payload, HTTP_IDEMPOTENCY_KEY=key) for _ in range(2)]
        self.assertEqual([r.status_code for r in responses], [201, 201])
        self.assertEqual(responses[0].json(), responses[1].json())
        self.assertEqual(MarketplaceOrder.objects.count(), 1)
        self.own.refresh_from_db(); self.assertEqual(self.own.stock, 8)
        legacy = MarketplaceOrder.objects.create(product_name="Isolated legacy order")
        from api.views import serialize_marketplace_order
        self.assertEqual(serialize_marketplace_order(legacy)["payment_method_label"], "Not recorded")

    def test_quote_checks_exact_required_variant_stock_and_server_price(self):
        product = self.product(self.owner, "Variant quote", customization_enabled=True, customization_options=[{
            "name": "Size", "selection": "single", "required": True, "options": [
                {"name": "Small", "stock": 10, "extra_price": "0"},
                {"name": "Large", "stock": 3, "extra_price": "5"}]}])
        item = self.item(product_id=product.pk)
        self.assertEqual(self.post("marketplace_checkout_quote", {"items": [item]}).status_code, 400)
        item["customization"] = {"selections": [{"group": "Size", "option": "Large", "extra_price": "999"}]}
        response = self.post("marketplace_checkout_quote", {"items": [item]})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["items"][0]["unit_price"], "25.00")
        self.assertEqual(self.post("marketplace_checkout_quote", {"items": [{**item, "quantity": 4}]}).status_code, 400)

    def test_bundle_quote_combines_component_stock_with_other_cart_lines_without_writes(self):
        bundle = self.product(self.owner, "Bundle quote", product_type="bundle")
        BundleComponent.objects.create(bundle=bundle, product=self.own, required_quantity=2)
        item = self.item(product_id=bundle.pk, quantity=4)
        response = self.post("marketplace_checkout_quote", {"items": [item]})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["items"][0]["available"], 5)
        self.assertEqual(self.post("marketplace_checkout_quote", {"items": [item, self.item(quantity=3)]}).status_code, 400)
        self.own.refresh_from_db(); self.assertEqual(self.own.stock, 10)
        self.assertFalse(MarketplaceOrder.objects.exists())
