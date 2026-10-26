"""Bundle recipes use real isolated database products, stock and order workflows."""
import json
import os
from pathlib import Path
from unittest.mock import patch
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from accounts.models import User, Department
from api.models import BundleComponent, MarketplaceOrder, Product
from api.views import serialize_product
from .services.bundles import describe_bundle, prime_bundle_inventory
from .services.inventory import get_product_inventory_snapshot, build_inventory_table
from modules.reports.dashboard_attention import inventory_attention_counts
from .services.analytics import _market_basket


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BundleProductTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(username="bundle-admin", password="CampusHub1!", role="Super Admin")
        cls.other = User.objects.create_user(username="other-bundle-owner", password="CampusHub1!")
        cls.department = Department.objects.create(name="Bundle Test Department", code="TEST-BUNDLE", is_program=True)

    def setUp(self):
        self.client.force_login(self.admin)
        self.products = [Product.objects.create(seller=self.admin, name=name, price=price, stock=stock, low_stock_threshold=2, approval_status="approved") for name, price, stock in [("Barbecue", 30, 20), ("Siomai", 10, 30), ("Banana Cue", 15, 12)]]
        self.recipe = [{"product_id": product.pk, "required_quantity": quantity, "selections": []} for product, quantity in zip(self.products, (1, 3, 1))]

    def save(self, **overrides):
        data = {"name":"Super Meal", "price":"65.00", "category":"Meals", "seller_id":self.admin.pk, "product_type":"bundle", "bundle_components":self.recipe, "tags":["Lunch", "Campus"], "department_id":self.department.pk}
        data.update(overrides)
        return self.client.post(reverse("admin_save_product"), json.dumps(data), content_type="application/json")

    def create_bundle(self, **overrides):
        response = self.save(**overrides)
        self.assertEqual(response.status_code, 201, response.content)
        return Product.objects.get(pk=response.json()["product"]["id"])

    def order(self, bundle, quantity=1):
        return self.client.post(reverse("marketplace_orders"), json.dumps({"product_id":bundle.pk, "buyer_user_id":self.admin.pk, "quantity":quantity}), content_type="application/json")

    def cancel(self, order_id):
        return self.client.post(reverse("admin_order_update", args=[order_id]), json.dumps({"status":"cancelled", "cancellation_reason":"Bundle test"}), content_type="application/json")

    def stocks(self):
        return list(Product.objects.filter(pk__in=[p.pk for p in self.products]).order_by("pk").values_list("stock", flat=True))

    def test_create_price_metadata_and_derived_availability(self):
        bundle = self.create_bundle()
        self.assertEqual((bundle.product_type, bundle.stock, bundle.low_stock_threshold, bundle.department_id, bundle.tags), ("bundle", 0, None, self.department.pk, ["Lunch", "Campus"]))
        self.assertFalse(bundle.customization_enabled)
        info = describe_bundle(bundle)
        self.assertEqual((info["available"], info["regular_price"], info["savings"]), (10, "75.00", "10.00"))
        snapshot = get_product_inventory_snapshot(bundle)
        assert snapshot is not None
        self.assertEqual((snapshot["on_hand"], snapshot["reserved"], snapshot["available"]), (None, None, 10))
        self.assertTrue(snapshot["derived"])

    def test_order_is_one_bundle_item_with_exact_component_holds(self):
        bundle = self.create_bundle()
        response = self.order(bundle)
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(self.stocks(), [19, 27, 11])
        order = MarketplaceOrder.objects.get()
        self.assertEqual((order.product_id, order.product_name, order.quantity, str(order.total_price)), (bundle.pk, "Super Meal", 1, "65.00"))
        self.assertEqual(len(order.customization["bundle_components"]), 3)
        self.assertEqual(bundle.get_total_stock(), 9)
        for product, original, reserved in zip(self.products, (20, 30, 12), (1, 3, 1)):
            product.refresh_from_db()
            snapshot = get_product_inventory_snapshot(product)
            assert snapshot is not None
            self.assertEqual((snapshot["on_hand"], snapshot["reserved"]), (original, reserved))
        bundle.refresh_from_db()
        self.assertEqual(bundle.stock, 0)

    def test_cancellation_restores_snapshot_once_even_if_recipe_changed_outside_ui(self):
        bundle = self.create_bundle()
        response = self.order(bundle, 2)
        order_id = response.json()["order"]["id"]
        BundleComponent.objects.filter(bundle=bundle, product=self.products[1]).update(required_quantity=1)
        self.assertEqual(self.cancel(order_id).status_code, 200)
        self.assertEqual(self.stocks(), [20, 30, 12])
        self.assertEqual(self.cancel(order_id).status_code, 200)
        self.assertEqual(self.stocks(), [20, 30, 12])
        self.assertTrue(MarketplaceOrder.objects.get().inventory_restored)

    def test_insufficient_bundle_order_is_atomic(self):
        bundle = self.create_bundle()
        self.assertEqual(self.order(bundle, 11).status_code, 409)
        self.assertEqual(self.stocks(), [20, 30, 12])
        self.assertFalse(MarketplaceOrder.objects.exists())

    def test_active_order_blocks_recipe_type_and_owner_changes(self):
        bundle = self.create_bundle()
        self.order(bundle)
        recipe = [{**row, "required_quantity":1} for row in self.recipe]
        response = self.save(id=bundle.pk, bundle_components=recipe)
        self.assertEqual(response.status_code, 400)
        self.assertIn("reserved orders", response.json()["error"])
        response = self.save(id=bundle.pk, product_type="single", bundle_components=[], stock=9, low_stock_threshold=2)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(bundle.bundle_components.get(product=self.products[1]).required_quantity, 3)

    def test_archived_bundle_holds_still_protect_component_type_changes(self):
        bundle = self.create_bundle()
        self.order(bundle)
        Product.objects.filter(pk=bundle.pk).update(is_archived=True)
        component = self.products[0]
        response = self.save(id=component.pk, bundle_components=[{"product_id":self.products[1].pk, "required_quantity":1}])
        self.assertEqual(response.status_code, 400)
        self.assertIn("component reservations", response.json()["error"])
        component.refresh_from_db()
        self.assertEqual(component.product_type, Product.TYPE_SINGLE)

    def test_rejects_cross_owner_unapproved_archived_and_unavailable_components(self):
        for changes in ({"seller":self.other}, {"approval_status":"pending"}, {"approval_status":"rejected"}, {"is_archived":True}, {"stock":0}):
            with self.subTest(changes=changes):
                product = self.products[0]
                Product.objects.filter(pk=product.pk).update(**changes)
                self.assertEqual(self.save().status_code, 400)
                Product.objects.filter(pk=product.pk).update(seller=self.admin, approval_status="approved", is_archived=False, stock=20)
        self.assertFalse(Product.objects.filter(product_type="bundle").exists())

    def test_rejects_invalid_quantities_empty_duplicate_nested_and_manual_stock(self):
        for quantity in (0, -1, 1.5, True):
            self.assertEqual(self.save(bundle_components=[{**self.recipe[0], "required_quantity":quantity}]).status_code, 400)
        for kwargs in ({"bundle_components":[]}, {"bundle_components":self.recipe + [self.recipe[0]]}, {"stock":3}, {"low_stock_threshold":2}, {"price":"NaN"}, {"price":"3.456"}):
            self.assertEqual(self.save(**kwargs).status_code, 400)
        bundle = self.create_bundle()
        self.assertEqual(self.save(bundle_components=[{"product_id":bundle.pk, "required_quantity":1}]).status_code, 400)
        self.assertEqual(self.save(id=bundle.pk, bundle_components=[{"product_id":bundle.pk, "required_quantity":1}]).status_code, 400)

    def test_exact_variant_availability_order_price_and_restore(self):
        drink = Product.objects.create(seller=self.admin, name="Campus Drink", price=20, stock=25, approval_status="approved", customization_enabled=True, customization_options=[{"name":"Size", "selection":"single", "required":True, "options":[{"name":"Small", "stock":20, "extra_price":"0", "low_stock_threshold":3}, {"name":"Large", "stock":5, "extra_price":"10", "low_stock_threshold":2}]}])
        self.recipe = [{"product_id":drink.pk, "required_quantity":2, "selections":[{"group":"Size", "option":"Large", "extra_price":"999"}]}]
        bundle = self.create_bundle(price="50.00")
        self.assertEqual((describe_bundle(bundle)["available"], describe_bundle(bundle)["regular_price"]), (2, "60.00"))
        response = self.order(bundle)
        self.assertEqual(response.status_code, 201)
        drink.refresh_from_db()
        self.assertEqual([row["stock"] for row in drink.customization_options[0]["options"]], [20, 3])
        snapshot = get_product_inventory_snapshot(drink)
        assert snapshot is not None
        self.assertEqual([row["reserved"] for row in snapshot["variant_thresholds"]], [0, 2])
        self.assertEqual(self.cancel(response.json()["order"]["id"]).status_code, 200)
        drink.refresh_from_db()
        self.assertEqual(drink.get_total_stock(), 25)

    def test_shared_variant_pool_demands_are_combined_before_reservation(self):
        product = self.products[0]
        product.customization_enabled = True
        product.customization_options = [
            {"name":"Size", "required":True, "options":[{"name":"Large", "stock":5, "extra_price":"0"}]},
            {"name":"Flavor", "required":True, "options":[{"name":"Vanilla", "stock":10, "extra_price":"0"}, {"name":"Chocolate", "stock":10, "extra_price":"0"}]}]
        product.save()
        self.recipe = [{"product_id":product.pk, "required_quantity":qty, "selections":[{"group":"Size", "option":"Large"}, {"group":"Flavor", "option":flavor}]} for flavor, qty in [("Vanilla", 2), ("Chocolate", 1)]]
        bundle = self.create_bundle()
        self.assertEqual(describe_bundle(bundle)["available"], 1)
        self.assertEqual(self.order(bundle, 2).status_code, 409)
        response = self.order(bundle)
        self.assertEqual(response.status_code, 201)
        product.refresh_from_db()
        self.assertEqual(product.customization_options[0]["options"][0]["stock"], 2)
        self.assertEqual([option["stock"] for option in product.customization_options[1]["options"]], [8, 9])
        self.assertEqual(self.cancel(response.json()["order"]["id"]).status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.customization_options[0]["options"][0]["stock"], 5)

    def test_expired_component_and_single_product_self_reference_rejected(self):
        from datetime import timedelta
        product = self.products[0]
        Product.objects.filter(pk=product.pk).update(category="Snacks", expiry_date=timezone.localdate() - timedelta(days=1))
        self.assertEqual(self.save().status_code, 400)
        Product.objects.filter(pk=product.pk).update(category="", expiry_date=None)
        self.assertEqual(self.save(id=str(product.pk)).status_code, 400)

    def test_inactive_owner_unavailable_and_bundle_threshold_never_used(self):
        bundle = self.create_bundle()
        User.objects.filter(pk=self.admin.pk).update(is_active=False)
        self.assertEqual(describe_bundle(bundle)["available"], 0)
        User.objects.filter(pk=self.admin.pk).update(is_active=True)
        Product.objects.filter(pk=self.products[0].pk).update(stock=1)
        bundle.refresh_from_db()
        self.assertEqual(serialize_product(bundle)["quantity_status"], "in_stock")
        self.assertIsNone(serialize_product(bundle)["low_stock_threshold"])

    def test_variant_selection_required_and_referenced_variant_cannot_be_removed(self):
        drink = self.products[0]
        drink.customization_enabled = True
        drink.customization_options = [{"name":"Size", "required":True, "options":[{"name":"Large", "stock":20, "extra_price":"0", "low_stock_threshold":2}]}]
        drink.save()
        self.assertEqual(self.save().status_code, 400)
        self.recipe[0]["selections"] = [{"group":"Size", "option":"Large"}]
        self.create_bundle()
        response = self.client.post(reverse("admin_save_product"), json.dumps({"id":drink.pk, "name":drink.name, "price":"30.00", "category":"Meals", "stock":20, "low_stock_threshold":2, "customization_enabled":False}), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("referencing bundle", response.json()["error"])

    def test_unreconcilable_selection_has_no_fake_price_or_wrong_restoration(self):
        product = self.products[0]
        product.customization_enabled = True
        product.customization_options = [{"name":"Size", "required":True, "options":[{"name":"Large", "stock":20, "extra_price":"5"}]}]
        product.save()
        self.recipe[0]["selections"] = [{"group":"Size", "option":"Large"}]
        bundle = self.create_bundle()
        order_id = self.order(bundle).json()["order"]["id"]
        product.refresh_from_db()
        product.customization_options[0]["options"][0]["name"] = "Renamed outside app"
        product.save()
        detail = describe_bundle(bundle)
        self.assertEqual(detail["available"], 0)
        self.assertIsNone(detail["regular_price"])
        self.assertIsNone(detail["savings"])
        self.assertEqual(self.cancel(order_id).status_code, 409)
        order = MarketplaceOrder.objects.get(pk=order_id)
        self.assertEqual(order.status, MarketplaceOrder.STATUS_PENDING)
        self.assertFalse(order.inventory_restored)
        self.assertEqual(self.stocks(), [19, 27, 11])

    def test_component_archival_disables_bundle_catalog_not_history(self):
        bundle = self.create_bundle()
        self.assertIn(bundle.pk, [p["id"] for p in self.client.get(reverse("approved_products")).json()["products"]])
        Product.objects.filter(pk=self.products[0].pk).update(is_archived=True)
        self.assertEqual(bundle.get_total_stock(), 0)
        self.assertNotIn(bundle.pk, [p["id"] for p in self.client.get(reverse("approved_products")).json()["products"]])
        self.assertEqual(self.order(bundle).status_code, 409)

    def test_inventory_views_derived_bundle_and_component_alerts(self):
        bundle = self.create_bundle()
        Product.objects.filter(pk=self.products[0].pk).update(stock=1)
        counts = inventory_attention_counts(timezone.localdate())
        self.assertEqual((counts["low_stock_products"], counts["out_of_stock_products"]), (1, 0))
        page = self.client.get(reverse("admin_products_page"))
        self.assertContains(page, "1 bundle available")
        ledger = self.client.get(reverse("admin_products_page"), {"view":"inventory", "product_id":bundle.pk})
        self.assertContains(ledger, "Derived from components")
        self.assertEqual(self.client.post(reverse("admin_update_product_stock", args=[bundle.pk]), json.dumps({"stock":100}), content_type="application/json").status_code, 400)

    def test_component_picker_filters_owners_status_and_expiry(self):
        self.create_bundle()
        Product.objects.create(seller=self.other, name="Other Owner", price=1, stock=10, approval_status="approved")
        Product.objects.create(seller=self.admin, name="Pending", price=1, stock=10)
        response = self.client.get(reverse("seller_products_monitor"), {"bundle_owner_id":self.admin.pk})
        self.assertEqual({p["id"] for p in response.json()["products"]}, {p.pk for p in self.products})
        self.client.logout()
        self.assertEqual(self.client.get(reverse("seller_products_monitor"), {"bundle_owner_id":self.admin.pk}).status_code, 302)

    def test_batch_inventory_and_catalog_have_constant_queries(self):
        for i in range(4): self.create_bundle(name=f"Meal {i}")
        with CaptureQueriesContext(connection) as queries:
            rows = prime_bundle_inventory(Product.objects.select_related("seller", "seller__department", "department"))
            [serialize_product(product) for product in rows]
        self.assertEqual(len(queries), 3)  # Products, stable SKU registry, bundle recipes.
        with CaptureQueriesContext(connection) as queries:
            ledger = build_inventory_table(Product.objects.all())
        self.assertEqual(len(queries), 4)
        self.assertEqual(len(ledger), 7)
        bundles = [row for row in ledger if row.get("derived")]
        self.assertEqual(len(bundles), 4)
        for row in bundles:
            self.assertEqual((row["on_hand"], row["reserved"], row["threshold"]), (None, None, None))
            self.assertEqual((row["available"], row["status_label"]), (10, "Available"))
        response = self.client.get(reverse("admin_products_page"), {"view": "inventory", "product_id": bundles[0]["product_id"]})
        self.assertContains(response, "<strong>Bundle</strong>")
        self.assertContains(response, "10 bundles</strong>")
        self.assertContains(response, ">Available</span>")
        directory = os.environ.get("INVENTORY_COLUMNS_REVIEW_DIR")
        if directory:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / "bundle-inventory.html").write_bytes(response.content)

    def test_apriori_basket_contains_bundle_identity_only(self):
        bundle = self.create_bundle()
        self.order(bundle)
        with patch("modules.marketplace.services.analytics.calculate_market_basket") as calculate:
            _market_basket(MarketplaceOrder.objects.all())
        baskets = list(calculate.call_args.args[0])
        self.assertEqual(baskets, [[(bundle.pk, "Super Meal")]])

    def test_completed_sales_rank_bundle_without_counting_ingredients(self):
        from modules.reports.dashboard_marketplace import top_selling_products
        bundle = self.create_bundle()
        response = self.order(bundle, 2)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        order.status = MarketplaceOrder.STATUS_COMPLETED
        order.payment_status = MarketplaceOrder.PAYMENT_PAID
        order.save()
        rows = top_selling_products(MarketplaceOrder.objects.filter(status="completed", payment_status="paid"))
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["product_name"], rows[0]["units_sold"], rows[0]["sales"]), ("Super Meal", 2, "130.00"))

    def test_export_real_test_database_for_form_review(self):
        directory = os.environ.get("BUNDLE_REVIEW_DIR")
        if not directory: return
        bundle = self.create_bundle()
        drink = Product.objects.create(seller=self.admin, name="Campus Drink", price=20, stock=25, approval_status="approved", customization_enabled=True, customization_options=[{"name":"Size", "required":True, "selection":"single", "options":[{"name":"Small", "stock":20, "extra_price":"0", "low_stock_threshold":3}, {"name":"Large", "stock":5, "extra_price":"10", "low_stock_threshold":2}]}])
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        (path / "form.html").write_bytes(self.client.get(reverse("admin_products_page")).content)
        (path / "catalog.json").write_text(json.dumps({"products":[serialize_product(p) for p in self.products + [drink]]}), encoding="utf-8")
        (path / "bundle.json").write_text(json.dumps(serialize_product(bundle, include_inventory=True)), encoding="utf-8")
