"""Per-option inventory through real order, stock-update and admin view workflows."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User, Department
from api.models import MarketplaceOrder, Product
from api.views import serialize_product
from .services.inventory import (
    InsufficientStockError, adjust_product_stock, build_inventory_table,
    get_product_inventory_snapshot, get_variant_stock_summary,
)
from modules.reports.dashboard_low_stock import build_low_stock_card


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ProductVariantInventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name":"Computing Program", "is_program":True})
        cls.admin = User.objects.create_superuser(username="variant-inventory-admin", password="CampusHub1!", role="Super Admin", department=program)

    def setUp(self):
        self.client.force_login(self.admin)
        self.product = Product.objects.create(seller=self.admin, name="Uniform", price=250, stock=19,
            approval_status=Product.STATUS_APPROVED, customization_enabled=True,
            customization_options=[{"name": "Size", "selection": "single", "required": True, "options": [
                {"name": "Small", "stock": 10, "low_stock_threshold": 3, "extra_price": "0"},
                {"name": "Medium", "stock": 5, "low_stock_threshold": 2, "extra_price": "0"},
                {"name": "Large", "stock": 4, "low_stock_threshold": 2, "extra_price": "20"}]}])

    def order(self, option="Large", quantity=3):
        return self.client.post(reverse("marketplace_orders"), json.dumps({"product_id": self.product.pk,
            "buyer_user_id": self.admin.pk, "quantity": quantity,
            "customization": [{"group": "Size", "option": option}]}), content_type="application/json")

    def snapshot(self):
        self.product.refresh_from_db()
        result = get_product_inventory_snapshot(self.product)
        assert result is not None, "Valid fixture must have reconcilable inventory."
        return result

    def save(self, **overrides):
        data = {"id": self.product.pk, "name": self.product.name, "price": str(self.product.price),
                "category": "Clothing", "customization_enabled": True,
                "customization_options": self.product.customization_options}
        data.update(overrides)
        return self.client.post(reverse("admin_save_product"), json.dumps(data), content_type="application/json")

    def test_order_deducts_reserves_and_prices_only_selected_variant(self):
        response = self.order()
        self.assertEqual(response.status_code, 201)
        snapshot = self.snapshot()
        rows = snapshot["variant_thresholds"]
        self.assertEqual([row["available"] for row in rows], [10, 5, 1])
        self.assertEqual([row["reserved"] for row in rows], [0, 0, 3])
        self.assertEqual([row["on_hand"] for row in rows], [10, 5, 4])
        self.assertEqual([row["threshold"] for row in rows], [3, 2, 2])
        self.assertEqual([row["status"] for row in rows], ["in_stock", "in_stock", "low_stock"])
        self.assertEqual((snapshot["available"], snapshot["reserved"], snapshot["on_hand"]), (16, 3, 19))
        self.assertEqual(response.json()["order"]["unit_price"], "270.00")
        self.assertEqual(get_variant_stock_summary(self.product)["low_stock_variant_count"], 1)

    def test_cancellation_restores_exact_variant_once(self):
        order = self.order().json()["order"]
        response = self.client.post(reverse("admin_order_update", args=[order["id"]]),
            json.dumps({"status": "cancelled", "cancellation_reason": "Inventory test"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["available"] for row in self.snapshot()["variant_thresholds"]], [10, 5, 4])
        self.assertEqual(self.snapshot()["reserved"], 0)
        response = self.client.post(reverse("admin_order_update", args=[order["id"]]),
            json.dumps({"status": "cancelled"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.snapshot()["available"], 19)

    def test_stock_update_requires_exact_variant_and_keeps_other_stock_and_holds(self):
        self.order()
        url = reverse("admin_update_product_stock", args=[self.product.pk])
        missing = self.client.post(url, json.dumps({"stock": 7}), content_type="application/json")
        self.assertEqual(missing.status_code, 400)
        response = self.client.post(url, json.dumps({"stock": 7, "variant_key": "0:2"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        rows = self.snapshot()["variant_thresholds"]
        self.assertEqual([row["available"] for row in rows], [10, 5, 7])
        self.assertEqual((rows[2]["reserved"], rows[2]["on_hand"], rows[2]["threshold"]), (3, 10, 2))

    def test_unknown_selection_never_deducts_or_restores_a_different_option(self):
        self.assertEqual(self.order(option="Missing").status_code, 400)
        self.assertEqual(self.snapshot()["available"], 19)
        self.product.customization_options[0]["options"] = [self.product.customization_options[0]["options"][0]]
        for restore in (False, True):
            with self.assertRaises(InsufficientStockError):
                adjust_product_stock(self.product, [{"group": "Size", "option": "Missing"}], 1, restore=restore)
        self.assertEqual(self.product.customization_options[0]["options"][0]["stock"], 10)

    def test_reserved_variant_cannot_be_renamed_removed_or_converted_to_parent(self):
        self.order()
        self.product.refresh_from_db()
        self.product.customization_options[0]["options"][2]["name"] = "Renamed"
        self.assertEqual(self.save().status_code, 400)
        self.product.refresh_from_db()
        self.product.customization_options[0]["options"].pop()
        self.assertEqual(self.save().status_code, 400)
        self.assertEqual(self.save(customization_enabled=False, customization_options=[], stock=16, low_stock_threshold=3).status_code, 400)
        self.assertEqual(self.snapshot()["variant_thresholds"][2]["reserved"], 3)

    def test_variant_stock_validation_and_duplicate_names(self):
        for value in (-1, "", "2.5", 2.5, True):
            with self.subTest(stock=value):
                self.product.customization_options[0]["options"][0]["stock"] = value
                self.assertEqual(self.save().status_code, 400)
        self.product.refresh_from_db()
        self.product.customization_options[0]["options"][1]["name"] = "Small"
        self.assertEqual(self.save().status_code, 400)
        self.assertEqual(self.snapshot()["available"], 19)

    def test_legacy_tracked_options_still_deduct_exact_variant_when_flag_is_false(self):
        self.product.customization_enabled = False
        self.product.save(update_fields=["customization_enabled"])
        self.assertEqual(self.order().status_code, 201)
        self.assertEqual([row["available"] for row in self.snapshot()["variant_thresholds"]], [10, 5, 1])

    def test_sold_out_option_keeps_other_variants_available_and_excludes_completed_holds(self):
        self.assertEqual(self.order(quantity=4).status_code, 201)
        self.assertEqual(self.product.get_inventory_status(), "in_stock")  # Unsaved original object.
        snapshot = self.snapshot()
        self.assertEqual(snapshot["variant_thresholds"][2]["status"], "out_of_stock")
        self.assertEqual(self.product.get_inventory_status(), "partially_available")
        self.assertEqual(self.order(option="Small", quantity=1).status_code, 201)
        MarketplaceOrder.objects.filter(product=self.product).update(status=MarketplaceOrder.STATUS_COMPLETED)
        self.assertEqual(self.snapshot()["reserved"], 0)

    def test_inventory_rows_list_summary_and_dashboard_use_same_variant(self):
        self.order()
        page = self.client.get(reverse("admin_products_page"))
        self.assertContains(page, "16 pcs")
        self.assertContains(page, "3 variants")
        self.assertContains(page, "1 variant Low Stock")
        inventory = self.client.get(reverse("admin_products_page"), {"view": "inventory"})
        rows = list(inventory.context["inventory_page"])
        self.assertEqual([row["available"] for row in rows], [10, 5, 1])
        self.assertEqual([row["reserved"] for row in rows], [0, 0, 3])
        for heading in ("Product", "Variant", "SKU", "Seller", "On Hand", "Reserved", "Available", "Threshold", "Status", "Last Updated", "Actions"):
            self.assertContains(inventory, f">{heading}</th>")
        self.assertNotContains(inventory, "Stock On Hand")
        self.assertEqual(len({row["sku"] for row in rows}), 3)
        self.assertEqual({row["seller_name"] for row in rows}, {self.admin.username})
        for row in rows:
            self.assertEqual(row["on_hand"] - row["reserved"], row["available"])
            self.assertEqual(row["updated_at"], inventory.context["inventory_page"][0]["updated_at"])
            self.assertContains(inventory, row["details_url"])
        filtered = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_status": "low_stock"})
        self.assertEqual([row["name"] for row in filtered.context["inventory_page"]], ["Large"])
        card = build_low_stock_card(today=timezone.localdate())["products"]
        self.assertEqual((card[0]["variant_name"], card[0]["available"], card[0]["threshold"]), ("Large", 1, 2))
        self.assertEqual(self.client.get(card[0]["url"]).status_code, 200)
        directory = os.environ.get("VARIANT_INVENTORY_REVIEW_DIR")
        if directory:
            self.product.refresh_from_db()
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            (path / "inventory.html").write_bytes(inventory.content)
            (path / "products.html").write_bytes(page.content)
            (path / "products.json").write_text(json.dumps([serialize_product(self.product, include_inventory=True)]), encoding="utf-8")

    def test_inventory_batches_reservations_and_preserves_simple_legacy_stock(self):
        self.order()
        self.product.refresh_from_db()
        simple = Product.objects.create(seller=self.admin, name="Simple", product_code="ADI-001", price=10, stock=7, low_stock_threshold=2)
        with self.assertNumQueries(3):
            rows = build_inventory_table(Product.objects.filter(pk__in=[self.product.pk, simple.pk]).order_by("pk"))
        self.assertEqual(len(rows), 4)
        self.assertEqual((rows[-1]["on_hand"], rows[-1]["reserved"], rows[-1]["available"], rows[-1]["threshold"]), (7, 0, 7, 2))
        self.assertTrue(rows[-1]["sku"].startswith("SIM-"))
        self.assertNotEqual(rows[-1]["sku"], simple.product_code)
        self.assertEqual(rows[-1]["name"], "")
        with self.assertNumQueries(3):
            build_inventory_table([self.product, simple])  # Missing sellers/SKUs load in batches.
        ordinary = User.objects.create_user(username="no-inventory-access")
        self.client.force_login(ordinary)
        self.assertEqual(self.client.get(reverse("admin_products_page"), {"view": "inventory"}).status_code, 302)

    def test_inventory_variant_skus_survive_reordering_and_stock_changes(self):
        before = {row["name"]: row["sku"] for row in build_inventory_table([self.product])}
        self.product.customization_options[0]["options"].reverse()
        self.product.customization_options[0]["options"][0]["stock"] = 0
        self.product.save(update_fields=["customization_options", "updated_at"])
        self.product.refresh_from_db()
        rows = build_inventory_table([self.product])
        self.assertEqual({row["name"]: row["sku"] for row in rows}, before)
        self.assertEqual(rows[0]["status"], "out_of_stock")
        self.assertEqual(rows[0]["updated_at"], self.product.updated_at)

    def test_option_image_stays_attached_when_other_option_has_no_image(self):
        import base64
        from io import BytesIO
        from PIL import Image
        buffer = BytesIO()
        Image.new('RGB', (2, 2), 'white').save(buffer, format='PNG')
        image = 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()
        self.product.customization_options[0]["options"][2]["image"] = image
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.save()
            self.assertEqual(response.status_code, 200)
            options = response.json()["product"]["customization_options"][0]["options"]
            self.assertNotIn("image", options[0])
            self.assertTrue(options[2]["image"].startswith("/media/"))
            self.assertTrue(list(Path(directory).rglob("*.png")))
            self.product.refresh_from_db()
            self.assertEqual(self.snapshot()["variant_thresholds"][2]["image_url"], options[2]["image"])

    def test_untracked_legacy_choice_does_not_create_fake_variant_inventory(self):
        self.product.customization_options[0]["options"].append({"name": "Legacy choice", "extra_price": "0"})
        self.product.save(update_fields=["customization_options"])
        snapshot = self.snapshot()
        assert snapshot is not None
        self.assertEqual([row["name"] for row in snapshot["variant_thresholds"]], ["Small", "Medium", "Large"])
        self.assertEqual(get_variant_stock_summary(self.product)["variant_count"], 3)
        self.assertEqual(self.product.get_inventory_status(), "in_stock")
        inventory = self.client.get(reverse("admin_products_page"), {"view": "inventory"})
        self.assertEqual(inventory.context["inventory_page"].paginator.count, 3)
