from decimal import Decimal
import json

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import Department, User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Product
from modules.marketplace.services.inventory import (
    InsufficientStockError,
    adjust_product_stock,
)


class ProductStockAdjustmentTests(SimpleTestCase):
    def test_simple_stock_is_reserved_and_restored(self):
        product = Product(stock=5)

        adjust_product_stock(product, [], 2)
        self.assertEqual(product.stock, 3)

        adjust_product_stock(product, [], 2, restore=True)
        self.assertEqual(product.stock, 5)

    def test_simple_stock_rejects_quantity_above_available(self):
        product = Product(stock=1)

        with self.assertRaisesRegex(InsufficientStockError, "Only 1 item"):
            adjust_product_stock(product, [], 2)

    def test_selected_variant_stock_is_reserved_and_restored(self):
        product = Product(
            stock=5,
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Size",
                    "selection": "single",
                    "required": True,
                    "options": [
                        {"name": "Regular", "stock": 3},
                        {"name": "Large", "stock": 2},
                    ],
                }
            ],
        )
        selections = [{"group": "Size", "option": "Large"}]

        adjust_product_stock(product, selections, 1)
        self.assertEqual(product.customization_options[0]["options"][1]["stock"], 1)
        self.assertEqual(product.stock, 4)

        adjust_product_stock(product, selections, 1, restore=True)
        self.assertEqual(product.customization_options[0]["options"][1]["stock"], 2)
        self.assertEqual(product.stock, 5)


class ProductPriceDisplayTests(SimpleTestCase):
    def test_product_without_variants_displays_base_price(self):
        product = Product(price=Decimal("50.00"))

        self.assertEqual(product.get_price_display(), "₱50.00")

    def test_required_single_variant_displays_price_range(self):
        product = Product(
            price=Decimal("50.00"),
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Size",
                    "selection": "single",
                    "required": True,
                    "options": [
                        {"name": "Regular", "extra_price": "0.00"},
                        {"name": "Large", "extra_price": "20.00"},
                    ],
                }
            ],
        )

        self.assertEqual(product.get_price_display(), "₱50.00 – ₱70.00")

    def test_required_and_optional_groups_use_valid_price_bounds(self):
        product = Product(
            price=Decimal("100.00"),
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Size",
                    "selection": "single",
                    "required": True,
                    "options": [
                        {"name": "Medium", "extra_price": "10.00"},
                        {"name": "Large", "extra_price": "25.00"},
                    ],
                },
                {
                    "name": "Add-ons",
                    "selection": "multiple",
                    "required": False,
                    "options": [
                        {"name": "Cheese", "extra_price": "15.00"},
                        {"name": "Egg", "extra_price": "10.00"},
                    ],
                },
            ],
        )

        self.assertEqual(product.get_price_display(), "₱110.00 – ₱150.00")


class ProductAdminInventoryAndPricingTests(SimpleTestCase):
    def test_product_without_variants_stock_and_status(self):
        from modules.marketplace.services.inventory import (
            get_product_total_stock,
            get_product_inventory_status,
            INVENTORY_STATUS_IN_STOCK,
            INVENTORY_STATUS_LOW_STOCK,
            INVENTORY_STATUS_OUT_OF_STOCK,
        )

        # Healthy stock
        p_healthy = Product(stock=41)
        self.assertEqual(get_product_total_stock(p_healthy), 41)
        self.assertEqual(get_product_inventory_status(p_healthy), INVENTORY_STATUS_IN_STOCK)

        # Low stock (<= 5)
        p_low = Product(stock=3)
        self.assertEqual(get_product_total_stock(p_low), 3)
        self.assertEqual(get_product_inventory_status(p_low), INVENTORY_STATUS_LOW_STOCK)

        # Zero stock
        p_zero = Product(stock=0)
        self.assertEqual(get_product_total_stock(p_zero), 0)
        self.assertEqual(get_product_inventory_status(p_zero), INVENTORY_STATUS_OUT_OF_STOCK)

        # Negative stock protection
        p_neg = Product(stock=-5)
        self.assertEqual(get_product_total_stock(p_neg), 0)

    def test_product_with_one_variant(self):
        from modules.marketplace.services.inventory import (
            get_product_total_stock,
            get_product_inventory_status,
            INVENTORY_STATUS_IN_STOCK,
        )

        p_one = Product(
            stock=0,
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Flavor",
                    "selection": "single",
                    "required": True,
                    "options": [{"name": "Vanilla", "stock": 10}],
                }
            ],
        )
        self.assertEqual(get_product_total_stock(p_one), 10)
        self.assertEqual(get_product_inventory_status(p_one), INVENTORY_STATUS_IN_STOCK)

    def test_product_with_multiple_variants_sums_stock(self):
        from modules.marketplace.services.inventory import (
            get_product_total_stock,
            get_product_inventory_status,
            INVENTORY_STATUS_IN_STOCK,
        )

        p_multi = Product(
            stock=0,
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Size",
                    "selection": "single",
                    "required": True,
                    "options": [
                        {"name": "Small", "stock": 15},
                        {"name": "Medium", "stock": 20},
                        {"name": "Large", "stock": 6},
                    ],
                }
            ],
        )
        self.assertEqual(get_product_total_stock(p_multi), 41)
        self.assertEqual(get_product_inventory_status(p_multi), INVENTORY_STATUS_IN_STOCK)

    def test_variants_with_same_price_displays_single_price(self):
        p_same_price = Product(
            price=Decimal("100.00"),
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Flavor",
                    "selection": "single",
                    "required": True,
                    "options": [
                        {"name": "Chocolate", "extra_price": "0.00"},
                        {"name": "Vanilla", "extra_price": "0.00"},
                        {"name": "Strawberry", "extra_price": "0.00"},
                    ],
                }
            ],
        )
        self.assertEqual(p_same_price.get_price_display(), "₱100.00")

    def test_variants_with_different_prices_displays_range(self):
        p_diff_price = Product(
            price=Decimal("80.00"),
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Size",
                    "selection": "single",
                    "required": True,
                    "options": [
                        {"name": "Regular", "extra_price": "0.00"},
                        {"name": "Large", "extra_price": "40.00"},
                    ],
                }
            ],
        )
        self.assertEqual(p_diff_price.get_price_display(), "₱80.00 – ₱120.00")

    def test_legacy_variants_without_stock_use_product_stock(self):
        from modules.marketplace.services.inventory import (
            INVENTORY_STATUS_OUT_OF_STOCK,
            get_product_inventory_status,
            get_product_total_stock,
        )

        product = Product(
            stock=0,
            category="Beverages",
            customization_enabled=True,
            customization_options=[
                {
                    "name": "Size",
                    "selection": "single",
                    "required": True,
                    "options": [
                        {"name": "Regular", "extra_price": "0.00"},
                        {"name": "Large", "extra_price": "20.00"},
                    ],
                }
            ],
        )

        self.assertEqual(get_product_total_stock(product), 0)
        self.assertEqual(
            get_product_inventory_status(product),
            INVENTORY_STATUS_OUT_OF_STOCK,
        )

    def test_approval_status_values(self):
        p_pending = Product(approval_status=Product.STATUS_PENDING)
        self.assertEqual(p_pending.approval_status, "pending")

        p_approved = Product(approval_status=Product.STATUS_APPROVED)
        self.assertEqual(p_approved.approval_status, "approved")

        p_rejected = Product(approval_status=Product.STATUS_REJECTED)
        self.assertEqual(p_rejected.approval_status, "rejected")


class MarketplaceAdminProductAccessTests(TestCase):
    password = "CampusHub1!"

    def setUp(self):
        admin_department = Department.objects.create(
            name="Marketplace Operations",
            code="MKT-OPS",
        )
        seller_department = Department.objects.create(
            name="Student Enterprise",
            code="STU-ENT",
        )
        self.marketplace_admin = User.objects.create_user(
            username="marketplace-products-admin",
            password=self.password,
            role="Marketplace Admin",
            department=admin_department,
            is_staff=True,
        )
        sync_user_admin_permissions(self.marketplace_admin)
        self.super_admin = User.objects.create_superuser(
            username="super-products-admin",
            password=self.password,
            email="super-products@example.com",
        )
        self.super_admin.role = "Super Admin"
        self.super_admin.save(update_fields=["role"])
        self.seller = User.objects.create_user(
            username="seller-products-owner",
            password=self.password,
            role="Seller",
            department=seller_department,
        )
        self.pending_product = Product.objects.create(
            seller=self.seller,
            name="Campus Sandwich",
            category="Snacks",
            price=Decimal("45.00"),
            stock=12,
            approval_status=Product.STATUS_PENDING,
        )
        self.low_stock_product = Product.objects.create(
            seller=self.seller,
            name="Campus Juice",
            category="Beverages",
            price=Decimal("30.00"),
            stock=3,
            approval_status=Product.STATUS_APPROVED,
        )

    def _product_page(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("admin_products_page"))

    def test_super_and_marketplace_admin_share_the_same_active_products(self):
        marketplace_response = self._product_page(self.marketplace_admin)
        super_response = self._product_page(self.super_admin)

        self.assertEqual(marketplace_response.status_code, 200)
        self.assertEqual(super_response.status_code, 200)
        marketplace_ids = {
            product.id for product in marketplace_response.context["seller_products"]
        }
        super_ids = {
            product.id for product in super_response.context["seller_products"]
        }
        expected_ids = {self.pending_product.id, self.low_stock_product.id}
        self.assertEqual(marketplace_ids, expected_ids)
        self.assertEqual(super_ids, expected_ids)

    def test_kpis_match_the_unfiltered_product_table(self):
        response = self._product_page(self.marketplace_admin)

        self.assertEqual(len(response.context["seller_products"]), 2)
        self.assertEqual(
            response.context["product_stats"],
            {
                "total": 2,
                "pending": 1,
                "approved": 1,
                "rejected": 0,
                "low_stock": 1,
                "archived": 0,
            },
        )
        self.assertContains(response, "Campus Sandwich")
        self.assertContains(response, "Student Enterprise")
        self.assertContains(response, 'id="productsSearchInput"')
        self.assertContains(response, 'id="productsStatusFilter"')
        self.assertContains(response, 'id="productsCategoryFilter"')

    def test_marketplace_admin_can_create_and_edit_product(self):
        self.client.force_login(self.marketplace_admin)
        create_response = self.client.post(
            reverse("admin_save_product"),
            data=json.dumps(
                {
                    "name": "Admin-owned Product",
                    "category": "Snacks",
                    "price": "25.00",
                    "stock": 5,
                }
            ),
            content_type="application/json",
        )
        edit_response = self.client.post(
            reverse("admin_save_product"),
            data=json.dumps(
                {
                    "id": self.pending_product.id,
                    "name": "Updated Campus Sandwich",
                    "category": "Snacks",
                    "price": "50.00",
                    "stock": 10,
                    "approval_status": Product.STATUS_PENDING,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(edit_response.status_code, 200)
        self.assertTrue(Product.objects.filter(name="Admin-owned Product").exists())
        self.pending_product.refresh_from_db()
        self.assertEqual(self.pending_product.name, "Updated Campus Sandwich")
        self.assertEqual(self.pending_product.seller, self.seller)

    def test_marketplace_page_shows_add_product_for_marketplace_admin_and_super_admin(self):
        marketplace_response = self._product_page(self.marketplace_admin)
        super_response = self._product_page(self.super_admin)

        self.assertContains(marketplace_response, 'id="addProductButton"')
        self.assertContains(super_response, 'id="addProductButton"')

    def test_listing_owner_shows_only_approved_sellers(self):
        response = self._product_page(self.marketplace_admin)

        self.assertContains(response, 'label="Approved Sellers"')
        self.assertContains(response, self.seller.username)
        self.assertNotContains(response, "Created Users")
        self.assertNotContains(response, "Administrators")
        self.assertNotContains(response, "created_users")
        self.assertNotIn("created_users", response.context)

    def test_unauthorized_user_cannot_approve_edit_or_archive(self):
        ordinary_user = User.objects.create_user(
            username="ordinary-products-user",
            password=self.password,
            role="User",
        )
        self.client.force_login(ordinary_user)

        approve_response = self.client.post(
            reverse("marketplace_approve_product", args=[self.pending_product.id])
        )
        edit_response = self.client.post(
            reverse("admin_save_product"),
            data=json.dumps(
                {
                    "id": self.pending_product.id,
                    "name": "Unauthorized Change",
                    "category": "Snacks",
                    "price": "45.00",
                    "stock": 12,
                }
            ),
            content_type="application/json",
        )
        archive_response = self.client.post(
            reverse("admin_archive_product", args=[self.pending_product.id])
        )

        self.assertEqual(approve_response.status_code, 403)
        self.assertEqual(edit_response.status_code, 403)
        self.assertEqual(archive_response.status_code, 403)
        self.pending_product.refresh_from_db()
        self.assertEqual(self.pending_product.name, "Campus Sandwich")
        self.assertFalse(self.pending_product.is_archived)

    def test_permanent_delete_is_disabled(self):
        self.client.force_login(self.marketplace_admin)

        response = self.client.post(
            reverse("admin_delete_product", args=[self.pending_product.id])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Product.objects.filter(id=self.pending_product.id).exists())

    def test_admin_products_page_uses_archive_instead_of_delete(self):
        self.client.force_login(self.marketplace_admin)
        response = self.client.get(reverse("admin_products_page"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "btn-archive-product")
        self.assertNotContains(response, "btn-delete-product")
        self.assertContains(response, 'id="archiveProductModal"')
        self.assertNotContains(response, 'id="deleteProductModal"')
        self.assertNotContains(response, 'id="pdMenuDeleteProduct"')

    def test_marketplace_admin_can_archive_and_restore_product(self):
        self.client.force_login(self.marketplace_admin)
        # Archive low_stock_product (approved)
        archive_response = self.client.post(
            reverse("admin_archive_product", args=[self.low_stock_product.id])
        )
        self.assertEqual(archive_response.status_code, 200)
        self.low_stock_product.refresh_from_db()
        self.assertTrue(self.low_stock_product.is_archived)

        # On admin products page, archived product has data-is-archived="1" and Restore button
        page_response = self.client.get(reverse("admin_products_page"))
        self.assertContains(page_response, f'data-product-id="{self.low_stock_product.id}"')
        self.assertContains(page_response, 'data-is-archived="1"')
        self.assertContains(page_response, 'btn-restore-product')

        # On public approved products API, archived product must NOT be returned
        public_response = self.client.get(reverse("approved_products"))
        self.assertEqual(public_response.status_code, 200)
        product_ids = [p["id"] for p in public_response.json().get("products", [])]
        self.assertNotIn(self.low_stock_product.id, product_ids)

        # Restoring product sets is_archived to False
        restore_response = self.client.post(
            reverse("admin_restore_product", args=[self.low_stock_product.id])
        )
        self.assertEqual(restore_response.status_code, 200)
        self.low_stock_product.refresh_from_db()
        self.assertFalse(self.low_stock_product.is_archived)

        # Once restored, admin page renders data-is-archived="0"
        restored_page = self.client.get(reverse("admin_products_page"))
        self.assertContains(restored_page, 'data-is-archived="0"')

        # And appears back in approved_products API
        restored_public = self.client.get(reverse("approved_products"))
        self.assertIn(self.low_stock_product.id, [p["id"] for p in restored_public.json().get("products", [])])

    def test_archived_product_preserves_order_history(self):
        from api.models import MarketplaceOrder
        buyer = User.objects.create_user(
            username="buyer-for-history",
            password=self.password,
            role="Student",
        )
        self.client.force_login(self.marketplace_admin)
        order = MarketplaceOrder.objects.create(
            buyer_user_id=buyer.id,
            buyer_name=buyer.username,
            seller_name=self.seller.username,
            product=self.low_stock_product,
            product_name=self.low_stock_product.name,
            quantity=2,
            unit_price=self.low_stock_product.price,
            total_price=self.low_stock_product.price * 2,
            status=MarketplaceOrder.STATUS_COMPLETED,
        )

        # Archive product with completed orders
        archive_resp = self.client.post(
            reverse("admin_archive_product", args=[self.low_stock_product.id])
        )
        self.assertEqual(archive_resp.status_code, 200)
        self.low_stock_product.refresh_from_db()
        self.assertTrue(self.low_stock_product.is_archived)

        # Historical order still references the archived product
        order.refresh_from_db()
        self.assertEqual(order.product_id, self.low_stock_product.id)
        self.assertEqual(order.product.name, self.low_stock_product.name)

        # Permanent delete is rejected (405)
        delete_resp = self.client.post(
            reverse("admin_delete_product", args=[self.low_stock_product.id])
        )
        self.assertEqual(delete_resp.status_code, 405)

    def test_seller_submission_keeps_seller_ownership(self):
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse("seller_submit_product"),
            data=json.dumps(
                {
                    "name": "Seller-created Snack",
                    "category": "Snacks",
                    "price": "20.00",
                    "stock": 8,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        product = Product.objects.get(name="Seller-created Snack")
        self.assertEqual(product.seller, self.seller)
        self.assertEqual(product.approval_status, Product.STATUS_PENDING)
