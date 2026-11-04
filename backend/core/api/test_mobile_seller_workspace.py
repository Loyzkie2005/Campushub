import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department
from api.models import CampusHubUser, Product, MarketplaceOrder, SellerRequest, SellerBundleSuggestion, BundleComponent
from modules.messages.auth import mobile_chat_token


class MobileSellerWorkspaceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        self.program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name":"Information Technology", "is_program":True})
        self.owner = self.account("workspace-owner")
        self.other = self.account("workspace-other")
        self.application = SellerRequest.objects.create(mobile_user=self.owner, status="approved")
        SellerRequest.objects.create(mobile_user=self.other, status="approved")
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + mobile_chat_token(self.owner)}
        self.own = self.product(self.owner, "Own Product")
        self.second = self.product(self.owner, "Second Product")
        self.foreign = self.product(self.other, "Other Seller Product")
        self.url = reverse("mobile_seller_workspace")

    def account(self, name):
        return CampusHubUser.objects.create(username=name, student_id=name, email=name+"@example.test",
            first_name="Test", last_name=name, password_hash="unused", user_type="student", role="User",
            department=self.program, profile_completed=True)

    def product(self, owner, name, **extra):
        return Product.objects.create(mobile_seller=owner, name=name, category="Snacks", price=Decimal("20"),
            stock=10, low_stock_threshold=2, approval_status="approved", **extra)

    def order(self, product, **extra):
        values = dict(product=product, product_name=product.name, quantity=2, unit_price=20,
            total_price=40, status="completed", payment_status="paid", completed_at=timezone.now())
        values.update(extra)
        return MarketplaceOrder.objects.create(**values)

    def get(self, **params):
        response = self.client.get(self.url, params, **self.auth)
        self.assertEqual(response.status_code, 200, response.content[:500])
        return response.json()

    def test_approved_seller_receives_own_simple_stock_and_retry_is_idempotent(self):
        from uuid import uuid4
        from api.models import InventoryBatch
        sku=self.own.inventory_skus.get(variant_name="")
        data={"sku":sku.pk,"quantity":3,"reference":"Seller receipt","key":str(uuid4()),"notes":"Own stock"}
        url=reverse("mobile_seller_receive_stock")
        first=self.client.post(url,json.dumps(data),content_type="application/json",**self.auth)
        self.assertEqual(first.status_code,200,first.content)
        self.assertEqual(self.client.post(url,json.dumps(data),content_type="application/json",**self.auth).json(),first.json())
        self.own.refresh_from_db();self.assertEqual(self.own.stock,13)
        self.assertFalse(InventoryBatch.objects.filter(sku=sku).exists())
        self.assertEqual(sku.movements.get(kind="receipt").actor,self.owner.get_full_name())

    def test_receiving_denies_foreign_stock_and_suspended_or_unapproved_sellers(self):
        from uuid import uuid4
        data={"sku":self.foreign.inventory_skus.get(variant_name="").pk,"quantity":1,"key":str(uuid4())}
        url=reverse("mobile_seller_receive_stock")
        self.assertEqual(self.client.post(url,json.dumps(data),content_type="application/json",**self.auth).status_code,409)
        data["sku"]=self.own.inventory_skus.get(variant_name="").pk
        self.application.is_suspended=True;self.application.save()
        self.assertEqual(self.client.post(url,json.dumps(data),content_type="application/json",**self.auth).status_code,403)
        self.assertIn(self.client.post(url,json.dumps(data),content_type="application/json").status_code,(401,403))
        self.foreign.refresh_from_db();self.own.refresh_from_db()
        self.assertEqual((self.foreign.stock,self.own.stock),(10,10))

    def test_all_workspace_data_is_owner_scoped_and_sales_are_paid_completed_only(self):
        self.order(self.own)
        self.order(self.own, payment_status="unpaid")
        self.order(self.own, status="pending")
        self.order(self.foreign, total_price=999)
        data = self.get(seller_id=self.other.pk)
        self.assertEqual({p["id"] for p in data["products"]}, {self.own.pk, self.second.pk})
        self.assertEqual({row["product_id"] for row in data["inventory"]}, {self.own.pk, self.second.pk})
        self.assertEqual(data["order_count"], 3)
        self.assertEqual(data["analytics"]["completed_orders"], 1)
        self.assertEqual(data["analytics"]["revenue"], "40.00")
        self.assertEqual(data["analytics"]["units_sold"], 2)
        self.assertNotIn("Other Seller Product", json.dumps(data))

    def test_sales_periods_use_philippine_today_week_and_month(self):
        manila = ZoneInfo("Asia/Manila")
        for paid_at in [datetime(2026, 10, 19, 0, 1, tzinfo=manila),
                        datetime(2026, 10, 18, 23, 59, tzinfo=manila),
                        datetime(2026, 10, 12, 12, tzinfo=manila),
                        datetime(2026, 9, 30, 12, tzinfo=manila)]:
            self.order(self.own, completed_at=paid_at)
        self.order(self.foreign, total_price=999,
                   completed_at=datetime(2026, 10, 19, 1, tzinfo=manila))
        with timezone.override(manila), patch(
            "modules.marketplace.services.analytics.timezone.localdate",
            return_value=date(2026, 10, 19),
        ):
            for period, revenue, start, count in [
                ("day", "40.00", "2026-10-19", 1),
                ("7", "80.00", "2026-10-13", 2),
                ("month", "120.00", "2026-10-01", 3),
            ]:
                with self.subTest(period=period):
                    data = self.get(period=period)["analytics"]
                    self.assertEqual(data["period"], period)
                    self.assertEqual(data["revenue"], revenue)
                    self.assertEqual(data["completed_orders"], count)
                    self.assertEqual(data["start"], start)
                    self.assertEqual(data["end"], "2026-10-19")

    def test_auth_approval_suspension_and_inactive_accounts_fail_closed(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        for status, suspended in [("pending", False), ("rejected", False), ("approved", True)]:
            SellerRequest.objects.filter(pk=self.application.pk).update(status=status, is_suspended=suspended)
            self.assertEqual(self.client.get(self.url, **self.auth).status_code, 403)
        SellerRequest.objects.filter(pk=self.application.pk).update(status="approved", is_suspended=False)
        self.owner.is_active = False
        self.owner.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(self.url, **self.auth).status_code, 403)

    def test_variant_rows_and_bundle_availability_reuse_inventory(self):
        variant = self.product(self.owner, "Variant Product", customization_enabled=True,
            customization_options=[{"name": "Size", "type": "radio", "required": True, "options": [
                {"name": "Small", "extra_price": "0", "stock": 6, "low_stock_threshold": 2},
                {"name": "Large", "extra_price": "0", "stock": 1, "low_stock_threshold": 2}]}])
        bundle = self.product(self.owner, "Own Bundle", product_type="bundle")
        BundleComponent.objects.create(bundle=bundle, product=self.own, required_quantity=2)
        rows = self.get()["inventory"]
        variants = [row for row in rows if row["product_id"] == variant.pk]
        self.assertEqual({row["name"]: row["available"] for row in variants}, {"Small": 6, "Large": 1})
        self.assertEqual(next(row for row in variants if row["name"] == "Large")["status"], "low_stock")
        derived = next(row for row in rows if row["product_id"] == bundle.pk)
        self.assertTrue(derived["derived"])
        self.assertEqual(derived["available"], 5)
        self.assertIsNone(derived["on_hand"])
        self.assertIsNone(derived["threshold"])

    def test_no_fake_recommendations_or_writes_on_reads(self):
        before = SellerBundleSuggestion.objects.count()
        with patch("modules.marketplace.services.bundle_suggestions.analyze_synthetic", side_effect=AssertionError("No CSV")):
            data = self.get()
        self.assertEqual(data["recommendations"]["rows"], [])
        self.assertEqual(data["saved_suggestions"], [])
        self.assertEqual(data["analytics"]["revenue"], "0.00")
        self.assertEqual(SellerBundleSuggestion.objects.count(), before)

    def fake_qualified_result(self):
        # Isolated presentation/authorization fixture, not production data/mining.
        return {"error": False, "message": "", "detail": "", "rows": [{
            "id": f"{self.own.pk}|{self.second.pk}", "seller": "Test seller",
            "products": [{"id": self.own.pk, "name": self.own.name, "image_url": ""},
                         {"id": self.second.pk, "name": self.second.name, "image_url": ""}]}]}

    def choice(self, pair, action):
        return self.client.post(reverse("mobile_seller_suggestion_choice", args=[pair]),
            json.dumps({"action": action}), content_type="application/json", **self.auth)

    def test_save_dismiss_remove_are_real_idempotent_and_cannot_cross_owners(self):
        pair = f"{self.own.pk}|{self.second.pk}"
        with patch("modules.marketplace.mobile_seller_views.live_suggestions", return_value=self.fake_qualified_result()):
            self.assertEqual(self.choice(pair, "save").status_code, 200)
            self.assertEqual(self.choice(pair, "save").status_code, 200)
            self.assertEqual(SellerBundleSuggestion.objects.count(), 1)
            self.assertEqual(len(self.get()["saved_suggestions"]), 1)
            self.assertEqual(self.choice(f"{self.own.pk}|{self.foreign.pk}", "save").status_code, 404)
            self.assertEqual(self.choice(pair, "dismiss").status_code, 200)
            self.assertEqual(self.get()["recommendations"]["rows"], [])
            self.assertEqual(self.get()["saved_suggestions"], [])
        self.assertEqual(self.choice(pair, "remove").status_code, 200)
        self.assertFalse(SellerBundleSuggestion.objects.exists())
        self.own.refresh_from_db()
        self.assertEqual(self.own.stock, 10)

    def test_cannot_save_arbitrary_or_invalid_pairs(self):
        self.assertEqual(self.choice(f"{self.own.pk}|{self.second.pk}", "save").status_code, 409)
        self.assertEqual(self.choice("bad", "save").status_code, 400)
        self.assertEqual(self.choice(f"{self.own.pk}|{self.own.pk}", "save").status_code, 400)
        self.assertEqual(self.choice(f"{self.own.pk}|{self.second.pk}", "approve").status_code, 400)
        self.assertFalse(SellerBundleSuggestion.objects.exists())

    def test_order_pagination_and_query_count_do_not_grow_per_row(self):
        self.order(self.own)
        with CaptureQueriesContext(connection) as first:
            self.get()
        for _ in range(31):
            self.order(self.own)
        with CaptureQueriesContext(connection) as many:
            data = self.get()
        self.assertLessEqual(len(many), len(first) + 2)
        self.assertEqual(len(data["orders"]), 30)
        self.assertEqual(data["orders_pages"], 2)
        self.assertEqual(len(self.get(orders_page=2)["orders"]), 2)

    def test_home_action_orders_are_owner_scoped_open_and_independent_of_recent_pages(self):
        open_orders = []
        for status in ("pending", "processing", "ready_for_pickup", "ready_for_pickup", "pending", "pending"):
            open_orders.append(self.order(self.own, status=status, payment_status="unpaid", completed_at=None))
        MarketplaceOrder.objects.filter(pk=open_orders[0].pk).update(created_at=timezone.now() - timedelta(days=90))
        MarketplaceOrder.objects.filter(pk=open_orders[3].pk).update(
            fulfillment_method="seller_delivery", delivery_started_at=timezone.now(), delivered_at=timezone.now())
        self.order(self.own, status="cancelled", payment_status="unpaid", completed_at=None)
        for _ in range(31):
            self.order(self.own)
        foreign = self.order(self.foreign, status="pending", payment_status="unpaid", completed_at=None)
        before = MarketplaceOrder.objects.count()
        data = self.get(period="day", seller_id=self.other.pk)
        action_ids = [row["id"] for row in data["orders_requiring_action"]]
        self.assertEqual(action_ids, [order.pk for order in open_orders[:5]])
        self.assertTrue(all(row["status_key"] == "completed" for row in data["orders"]))
        self.assertNotIn(foreign.pk, action_ids)
        self.assertEqual(data["orders_requiring_action"][3]["fulfillment_progress"], "Delivered")
        self.assertEqual(data["orders_requiring_action"][3]["payment_status"], "Unpaid")
        self.assertEqual([row["id"] for row in self.get(orders_page=2)["orders_requiring_action"]], action_ids)
        self.assertEqual(MarketplaceOrder.objects.count(), before)

    def test_recent_orders_are_newest_owner_records_of_every_status_on_every_page(self):
        older = timezone.now() - timedelta(days=90)
        for _ in range(31):
            order = self.order(self.own, completed_at=older)
            MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=older)
        recorded_at = timezone.now() - timedelta(days=3)
        statuses = ("pending", "processing", "ready_for_pickup", "cancelled", "completed")
        latest = []
        for status in statuses:
            order = self.order(self.own, status=status, buyer_name="Recorded Buyer " + status,
                payment_status="paid" if status == "completed" else "unpaid",
                completed_at=recorded_at if status == "completed" else None)
            MarketplaceOrder.objects.filter(pk=order.pk).update(created_at=recorded_at)
            latest.append(order)
        foreign = self.order(self.foreign, buyer_name="Foreign Buyer")
        before = MarketplaceOrder.objects.count()
        data = self.get(period="day", seller_id=self.other.pk)
        recent = data["recent_orders"]
        self.assertEqual([row["id"] for row in recent], [row.pk for row in reversed(latest)])
        self.assertEqual({row["status_key"] for row in recent}, set(statuses))
        self.assertEqual(recent, data["orders"][:5])
        self.assertEqual(data["order_count"], 36)
        self.assertEqual(data["analytics"]["revenue"], "0.00")
        self.assertNotIn(foreign.pk, [row["id"] for row in recent])
        for row in recent:
            self.assertTrue({"id", "code", "buyer_name", "status", "total", "created_at", "payment_status"} <= row.keys())
            self.assertEqual(row["buyer_name"], "Recorded Buyer " + row["status_key"])
            self.assertEqual(row["payment_status"], "Paid" if row["status_key"] == "completed" else "Unpaid")
            self.assertEqual(Decimal(row["total"]), Decimal("40"))
        second_page = self.get(period="month", orders_page=2)
        self.assertEqual(second_page["recent_orders"], recent)
        self.assertNotEqual(second_page["orders"][:5], recent)
        self.assertEqual(MarketplaceOrder.objects.count(), before)

    def test_recent_preview_uses_buyer_full_name_and_purchased_product_snapshot(self):
        buyer = self.account("short-buyer-handle")
        buyer.first_name, buyer.last_name = "Alexandria Maria", "Dela Cruz"
        buyer.save(update_fields=["first_name", "last_name"])
        order = self.order(self.own, buyer_user_id=buyer.pk, buyer_email=buyer.email.upper(),
            buyer_name=buyer.username, product_name="Purchased Full Product Name", quantity=3,
            total_price=60, image_url="/media/orders/purchased-thumbnail.png")
        self.own.name, self.own.price, self.own.image_url = "Renamed Current Product", 999, "/media/products/new.png"
        self.own.save()
        before = (MarketplaceOrder.objects.count(), self.own.stock)
        row = self.get()["recent_orders"][0]
        self.assertEqual(row["buyer_full_name"], "Alexandria Maria Dela Cruz")
        self.assertEqual(row["buyer_name"], buyer.username)
        self.assertEqual(row["product_preview"], {"product_name": "Purchased Full Product Name",
            "quantity": 3, "thumbnail_url": "/media/orders/purchased-thumbnail.png", "additional_items": 0})
        self.assertEqual(Decimal(row["total"]), Decimal("60"))
        order.refresh_from_db(); self.own.refresh_from_db()
        self.assertEqual((MarketplaceOrder.objects.count(), self.own.stock), before)
        self.assertEqual(order.buyer_name, buyer.username)

    def test_preview_names_do_not_confuse_web_and_mobile_accounts_with_equal_ids(self):
        from accounts.models import User
        buyer = self.account("mobile-buyer-identity")
        web = User.objects.create_user(pk=buyer.pk, username="separate-web-buyer",
            first_name="Actual Web", last_name="Buyer", email="web-buyer@example.test")
        matched = self.order(self.own, buyer_user_id=buyer.pk, buyer_email=web.email, buyer_name="Short")
        ambiguous = self.order(self.own, buyer_user_id=buyer.pk, buyer_name="Recorded Buyer Snapshot")
        rows = {row["id"]: row for row in self.get()["recent_orders"]}
        self.assertEqual(rows[matched.pk]["buyer_full_name"], "Actual Web Buyer")
        self.assertEqual(rows[ambiguous.pk]["buyer_full_name"], "Recorded Buyer Snapshot")

    def test_product_preview_keeps_item_names_quantities_and_bundle_identity(self):
        from modules.marketplace.services.mobile_order_previews import product_preview
        from modules.marketplace.services.orders import order_items
        historical = self.order(self.own, customization={"items": [
            {"product_name": "First Purchased Product", "quantity": 2, "image_url": "/media/item-one.png"},
            {"product_name": "Second Purchased Product", "quantity": 4}]})
        self.assertEqual(product_preview(historical, order_items(historical)), {
            "product_name": "First Purchased Product", "quantity": 2,
            "thumbnail_url": "/media/item-one.png", "additional_items": 1})
        bundle = self.order(self.own, product_name="Purchased Bundle", quantity=3,
            customization={"bundle_components": [{"product_id": self.own.pk}], "items": [
                {"product_name": "Ingredient", "quantity": 9}, {"product_name": "Other ingredient", "quantity": 6}]})
        preview = product_preview(bundle, order_items(bundle))
        self.assertEqual((preview["product_name"], preview["quantity"], preview["additional_items"]), ("Purchased Bundle", 3, 0))
        # The existing owner scope excludes ambiguous legacy multi-item records.
        ids = {row["id"] for row in self.get()["recent_orders"]}
        self.assertNotIn(historical.pk, ids)
        self.assertNotIn(bundle.pk, ids)

    def test_linked_buyer_lookup_has_constant_query_growth(self):
        buyer = self.account("batched-order-buyer")
        self.order(self.own, buyer_user_id=buyer.pk, buyer_email=buyer.email)
        with CaptureQueriesContext(connection) as first:
            self.get()
        for _ in range(31):
            self.order(self.own, buyer_user_id=buyer.pk, buyer_email=buyer.email)
        with CaptureQueriesContext(connection) as many:
            self.get()
        self.assertLessEqual(len(many), len(first) + 2)

    def bundle_payload(self):
        return {"name": "Test submitted bundle", "price": "30.00", "category": "Snacks", "product_type": "bundle",
                "suggestion_id": f"{self.own.pk}|{self.second.pk}", "bundle_components": [
                    {"product_id": self.own.pk, "required_quantity": 2},
                    {"product_id": self.second.pk, "required_quantity": 1}]}

    def submit_bundle(self, data):
        return self.client.post(reverse("seller_submit_product"), json.dumps(data), content_type="application/json", **self.auth)

    def test_mobile_bundle_submission_reuses_recipe_stock_and_product_approval(self):
        from api.models import BundleRecommendation
        from accounts.models import AccountActivity
        suggestion = BundleRecommendation.objects.create(product_a=self.own, product_b=self.second)
        with patch("modules.marketplace.services.bundle_suggestions.build_bundle_suggestions", return_value=self.fake_qualified_result()):
            response = self.submit_bundle(self.bundle_payload())
        self.assertEqual(response.status_code, 201, response.content)
        product = Product.objects.get(pk=response.json()["product"]["id"])
        self.assertEqual(product.mobile_seller_id, self.owner.pk)
        self.assertEqual(product.product_type, "bundle")
        self.assertEqual(product.approval_status, "pending")
        self.assertEqual(product.source_recommendation_id, suggestion.pk)
        self.assertEqual(AccountActivity.objects.filter(activity_type="BUNDLE_CREATED_FROM_SUGGESTION",
            metadata__recommendation_id=suggestion.pk).count(), 1)
        self.assertEqual(product.stock, 0)
        self.assertIsNone(product.low_stock_threshold)
        self.assertEqual(product.bundle_components.count(), 2)
        # Canonical inventory keeps a bundle SKU identity, but no stock pool/movement.
        self.assertTrue(product.inventory_skus.exists())
        self.assertFalse(product.inventory_skus.filter(movements__isnull=False).exists())
        self.assertEqual(response.json()["product"]["stock"], 5)
        self.own.refresh_from_db()
        self.assertEqual(self.own.stock, 10)
        data = self.get()
        self.assertEqual(data["overview"]["active_products"], 2)
        self.assertEqual(data["bundle_submissions"][0]["approval_status"], "pending")

    def test_mobile_bundle_rejects_forged_pairs_foreign_owner_and_standalone_stock(self):
        before = Product.objects.count()
        self.assertEqual(self.submit_bundle(self.bundle_payload()).status_code, 400)
        with patch("modules.marketplace.services.bundle_suggestions.build_bundle_suggestions", return_value=self.fake_qualified_result()):
            data = self.bundle_payload(); data["bundle_components"][1]["product_id"] = self.foreign.pk
            self.assertEqual(self.submit_bundle(data).status_code, 400)
            data = self.bundle_payload(); data["stock"] = 10
            self.assertEqual(self.submit_bundle(data).status_code, 400)
            data = self.bundle_payload(); data["suggestion_id"] = "invalid"
            self.assertEqual(self.submit_bundle(data).status_code, 400)
        self.assertEqual(Product.objects.count(), before)
        self.assertFalse(BundleComponent.objects.exists())

    def test_mobile_bundle_requires_exact_stock_variant(self):
        self.own.customization_enabled = True
        self.own.customization_options = [{"name": "Size", "selection": "single", "required": True,
            "options": [{"name": "Small", "extra_price": "0", "stock": 6}, {"name": "Large", "extra_price": "0", "stock": 1}]}]
        self.own.save()
        data = self.bundle_payload(); data["bundle_components"][0]["required_quantity"] = 1
        with patch("modules.marketplace.services.bundle_suggestions.build_bundle_suggestions", return_value=self.fake_qualified_result()):
            self.assertEqual(self.submit_bundle(data).status_code, 400)
            data["bundle_components"][0]["selections"] = [{"group": "Size", "option": "Large"}]
            response = self.submit_bundle(data)
            self.assertEqual(response.status_code, 201, response.content)
            self.assertEqual(response.json()["product"]["stock"], 1)

    def test_overview_counts_are_actual_and_owner_scoped(self):
        self.order(self.own, status="pending", payment_status="unpaid")
        self.order(self.foreign, status="pending", payment_status="unpaid")
        self.order(self.own)
        self.second.is_archived = True; self.second.save()
        data = self.get()
        self.assertEqual(data["order_count"], 2)
        self.assertEqual(data["overview"], {"active_products": 1, "completed_orders": 1, "pending_orders": 1})
