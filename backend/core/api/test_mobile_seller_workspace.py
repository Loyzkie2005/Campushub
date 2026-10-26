import json
from datetime import date, datetime
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
