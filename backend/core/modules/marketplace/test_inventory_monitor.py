"""Real inventory filters, persistent SKU identity, recorded history and access."""
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse

from accounts.models import Department, User
from api.models import BundleComponent, InventorySKU, InventoryStockMovement, MarketplaceOrder, Product
from .services.inventory import build_inventory_table


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class InventoryMonitorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(username="inventory-monitor-admin", password="CampusHub1!", role="Super Admin")
        cls.it = Department.objects.create(name="Computing Test", code="CT", is_program=True)
        cls.food = Department.objects.create(name="Food Test", code="FT", is_program=True)
        cls.seller = User.objects.create_user(username="inventory-owner", first_name="Test", last_name="Seller", department=cls.it)
        cls.other = User.objects.create_user(username="another-owner", department=cls.food)

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse("admin_products_page")
        self.product = Product.objects.create(seller=self.seller, name="Uniform", price=250, stock=16,
            category="Clothing", product_code="PRD-0041", approval_status="approved", customization_enabled=True,
            customization_options=[{"name":"Size", "selection":"single", "required":True, "options":[
                {"name":"Small", "stock":10, "low_stock_threshold":3},
                {"name":"Medium", "stock":5, "low_stock_threshold":2},
                {"name":"Large", "stock":1, "low_stock_threshold":2}]}])
        self.simple = Product.objects.create(seller=self.other, name="Adidas", price=100, stock=20, category="Sports", low_stock_threshold=5, approval_status="approved")
        self.zero = Product.objects.create(seller=self.seller, name="Notebook", price=10, stock=0, category="Supplies", low_stock_threshold=3, approval_status="approved")

    def page(self, **params):
        return self.client.get(self.url, {"view":"inventory", **params})

    def order(self, product=None, **data):
        payload = {"product_id":(product or self.product).pk, "buyer_user_id":self.admin.pk, "quantity":1,
                   "customization":[{"group":"Size", "option":"Small"}]}
        payload.update(data)
        response = self.client.post(reverse("marketplace_orders"), json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content)
        return MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])

    def test_skus_are_persistent_readable_distinct_from_product_id_and_unique(self):
        rows = list(self.page().context["inventory_page"])
        codes = [row["sku"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(not code.startswith("PRD-") for code in codes))
        uniforms = [row for row in rows if row["product_id"] == self.product.pk]
        self.assertTrue(all(row["sku"].startswith("UNI-") for row in uniforms))
        before = {row["name"]:row["sku"] for row in uniforms}
        self.product.name = "Renamed Uniform"
        self.product.product_code = "PRD-9999"
        self.product.customization_options[0]["options"].reverse()
        self.product.save()
        after = build_inventory_table(Product.objects.filter(pk=self.product.pk))
        self.assertEqual({row["name"]:row["sku"] for row in after}, before)
        identity = self.product.inventory_skus.get(variant_name="Small")
        with self.assertRaises(IntegrityError), transaction.atomic():
            InventorySKU.objects.create(product=self.product, group_name=identity.group_name, variant_name=identity.variant_name, prefix="XXX")

    def test_search_is_variant_and_sku_specific_and_supports_owner_name(self):
        small = self.product.inventory_skus.get(variant_name="Small")
        for search in ("Small", small.code.lower()):
            response = self.page(search=search)
            self.assertEqual([row["name"] for row in response.context["inventory_page"]], ["Small"])
        self.assertEqual(self.page(search="Test Seller").context["inventory_summary"]["total"], 4)
        self.assertEqual(self.page(search="PRD-0041").context["inventory_summary"]["total"], 0)

    def test_all_filters_intersect_and_product_department_overrides_seller(self):
        params = {"program":self.it.pk, "seller":self.seller.pk, "category":"Clothing", "inventory_status":"low_stock", "search":"Uniform"}
        response = self.page(**params)
        self.assertEqual([row["name"] for row in response.context["inventory_page"]], ["Large"])
        for key in ("program", "seller", "category", "inventory_status", "search"):
            self.assertEqual(parse_qs(response.context["page_query"])[key], [str(params[key])])
        self.assertContains(response, f'value="{self.it.pk}" selected')
        Product.objects.filter(pk=self.product.pk).update(department=self.food)
        self.assertEqual(self.page(**params).context["inventory_summary"]["total"], 0)
        self.assertEqual(self.page(department=self.food.pk, seller=self.seller.pk).context["inventory_summary"]["total"], 3)

    def test_dynamic_filter_choices_ignore_nonmarketplace_users_and_archived_categories(self):
        irrelevant = User.objects.create_user(username="no-products")
        Product.objects.create(seller=self.other, name="Archived", price=10, stock=5, category="Old category", is_archived=True)
        response = self.page()
        self.assertEqual({user.pk for user in response.context["inventory_sellers"]}, {self.seller.pk, self.other.pk})
        self.assertNotIn(irrelevant.pk, {user.pk for user in response.context["inventory_sellers"]})
        self.assertEqual(set(response.context["inventory_categories"]), {"Clothing", "Sports", "Supplies"})
        self.assertEqual({department.pk for department in response.context["inventory_departments"]}, set(Department.objects.filter(is_program=True).values_list("pk", flat=True)))

    def test_summary_uses_real_filtered_rows_and_exact_reservation(self):
        self.order(quantity=2)
        summary = self.page().context["inventory_summary"]
        self.assertEqual(summary, {"total":5, "low_stock":1, "out_of_stock":1, "reserved":2})
        filtered = self.page(inventory_status="low_stock").context["inventory_summary"]
        self.assertEqual(filtered, {"total":1, "low_stock":1, "out_of_stock":0, "reserved":0})

    def test_pagination_and_detail_back_link_preserve_filters_reset_clears_them(self):
        for index in range(31):
            Product.objects.create(seller=self.seller, name=f"Uniform spare {index}", price=10, stock=1, low_stock_threshold=2, category="Clothing")
        params = {"seller":self.seller.pk, "category":"Clothing", "inventory_status":"low_stock", "search":"Uniform"}
        response = self.page(**params)
        self.assertTrue(response.context["inventory_page"].has_next())
        row = response.context["inventory_page"][0]
        detail = self.client.get(row["inventory_url"])
        back = parse_qs(urlparse(detail.context["inventory_return_url"]).query)
        for key, value in params.items():
            self.assertEqual(back[key], [str(value)])
        self.assertContains(detail, 'name="seller"')
        self.assertContains(detail, f'href="{self.url}?view=inventory">Clear Filters')

    def test_detail_is_readonly_variant_specific_and_shows_recorded_adjustment(self):
        sku = self.product.inventory_skus.get(variant_name="Large")
        response = self.client.post(reverse("admin_update_product_stock", args=[self.product.pk]), json.dumps({"stock":4, "variant_key":"0:2"}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        detail = self.page(inventory_item=sku.pk)
        item = detail.context["inventory_detail"]
        self.assertEqual((item["on_hand"], item["reserved"], item["available"], item["threshold"]), (4, 0, 4, 2))
        adjustment = sku.movements.get(kind="adjustment")
        self.assertEqual((adjustment.quantity_change, adjustment.available_before, adjustment.available_after, adjustment.actor), (3, 1, 4, self.admin.username))
        self.assertContains(detail, "Stock Movement History")
        self.assertNotContains(detail, "Add Stock")
        self.assertEqual(self.product.inventory_skus.get(variant_name="Small").movements.filter(kind="adjustment").count(), 0)

    def test_reservation_release_and_sale_events_do_not_double_deduct(self):
        sku = self.product.inventory_skus.get(variant_name="Small")
        order = self.order(quantity=2)
        self.assertEqual(sku.movements.get(kind="reservation", order=order).quantity_change, -2)
        cancel = self.client.post(reverse("admin_order_update", args=[order.pk]), json.dumps({"status":"cancelled", "cancellation_reason":"Test"}), content_type="application/json")
        self.assertEqual(cancel.status_code, 200)
        self.assertEqual(sku.movements.get(kind="release", order=order).quantity_change, 2)
        order = self.order(quantity=2)
        for status in ("processing", "ready_for_pickup", "completed"):
            response = self.client.post(reverse("admin_order_update", args=[order.pk]), json.dumps({"status":status, "payment_status":"paid", "pickup_confirmed": status == "completed", "official_receipt_no":"TEST-OR"}), content_type="application/json")
            self.assertEqual(response.status_code, 200, response.content)
        sale = sku.movements.get(kind="sale", order=order)
        self.assertEqual((sale.quantity_change, sale.balance), (-2, "on_hand"))
        detail = self.page(inventory_item=sku.pk).context["inventory_detail"]
        self.assertEqual((detail["on_hand"], detail["reserved"], detail["available"]), (8, 0, 8))
        self.assertEqual(len([event for event in detail["movements"] if event["reference"] == "Order #" + order.order_code]), 2)

    def test_legacy_history_never_invents_restock_or_opening_stock(self):
        sku = self.simple.inventory_skus.get(variant_name="")
        sku.movements.all().delete()  # Simulates a pre-migration SKU: no old restock audit.
        Product.objects.filter(pk=self.simple.pk).update(stock=18)
        MarketplaceOrder.objects.create(product=self.simple, product_name=self.simple.name, quantity=2, unit_price=100, total_price=200, inventory_deducted=True)
        item = self.page(inventory_item=sku.pk).context["inventory_detail"]
        self.assertEqual([event["kind"] for event in item["movements"]], ["Reservation"])
        self.assertNotIn("before", item["movements"][0])

    def test_bundle_sku_and_history_use_exact_components_without_fake_parent_stock(self):
        bundle = Product.objects.create(seller=self.seller, name="Meal", price=100, stock=0, product_type="bundle", approval_status="approved")
        BundleComponent.objects.create(bundle=bundle, product=self.product, required_quantity=2, selections=[{"group":"Size", "option":"Small"}])
        sku = bundle.inventory_skus.get(variant_name="")
        self.assertTrue(sku.code.startswith("BND-"))
        item = self.page(inventory_item=sku.pk).context["inventory_detail"]
        self.assertEqual((item["on_hand"], item["reserved"], item["threshold"], item["available"]), (None, None, None, 5))
        directory = os.environ.get("INVENTORY_MONITOR_REVIEW_DIR")
        if directory:
            root = Path(directory); root.mkdir(parents=True, exist_ok=True)
            (root / "bundle.html").write_bytes(self.page(inventory_item=sku.pk).content)
        order = self.order(product=bundle, customization=[])
        small = self.product.inventory_skus.get(variant_name="Small")
        self.assertEqual(small.movements.get(kind="reservation", order=order).quantity_change, -2)
        self.assertFalse(sku.movements.exists())

    def test_archived_history_is_retained_and_unauthorized_details_are_denied(self):
        sku = self.simple.inventory_skus.get(variant_name="")
        self.simple.archive()
        self.assertFalse(any(row["product_id"] == self.simple.pk for row in self.page().context["inventory_page"]))
        self.assertTrue(self.page(inventory_item=sku.pk).context["inventory_detail"]["archived"])
        self.client.force_login(self.seller)
        self.assertEqual(self.page(inventory_item=sku.pk).status_code, 302)
        self.client.force_login(self.admin)
        self.assertEqual(self.page(inventory_item="invalid").status_code, 404)

    def test_empty_state_and_export_actual_fixture_html(self):
        empty = self.page(search="does not exist")
        self.assertContains(empty, "No inventory records match the selected filters.")
        self.assertContains(empty, "Clear Filters")
        directory = os.environ.get("INVENTORY_MONITOR_REVIEW_DIR")
        if directory:
            root = Path(directory); root.mkdir(parents=True, exist_ok=True)
            import base64
            image = Path(__file__).resolve().parents[3] / 'static/assets/img/icon.png'
            source = 'data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode()
            self.simple.image_url = source
            self.simple.save(update_fields=['image_url'])
            self.product.image_url = source
            self.product.customization_options[0]['options'][2]['image'] = source
            self.product.save(update_fields=['image_url', 'customization_options'])
            root.joinpath('inventory-images.json').write_text(json.dumps({reverse('product_image', args=[p.pk]): source for p in (self.simple,self.product)}), encoding='utf-8')
            sku = self.product.inventory_skus.get(variant_name="Large")
            for name, response in (("inventory", self.page()), ("detail", self.page(inventory_item=sku.pk)), ("empty", empty)):
                (root / f"{name}.html").write_bytes(response.content)
            (root / "inventory-product.html").write_bytes(self.client.get(self.url, {"product_id": self.product.pk}).content)
            (root / "inventory-products.json").write_text(json.dumps(self.client.get(reverse("seller_products_monitor")).json()), encoding="utf-8")

    def test_visible_actions_keep_existing_destinations_and_permission_gates(self):
        from html.parser import HTMLParser
        from django.contrib.auth.models import Permission

        class ActionLinks(HTMLParser):
            def __init__(self, content):
                super().__init__()
                self.links = []
                self.feed(content.decode())

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "a" and "inventory-icon-action" in attrs.get("class", "").split():
                    self.links.append(attrs)

        response = self.page(search="Uniform")
        links = ActionLinks(response.content).links
        expected = []
        for row in response.context["inventory_page"]:
            expected.extend([(row["inventory_url"] + "#inventory-details", "View Details"),
                             (row["movements_url"], "Stock Movements"), (row["details_url"], "View Product")])
        self.assertEqual([(link["href"], link["title"]) for link in links], expected)
        self.assertTrue(all("Uniform" in link["aria-label"] for link in links))
        self.assertNotContains(response, 'class="inventory-actions-menu"')
        for link in links:
            self.assertEqual(self.client.get(link["href"]).status_code, 200)

        viewer = User.objects.create_user(username="inventory-only-viewer", is_staff=True, department=self.it)
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label="accounts", codename="can_view_inventory"))
        self.client.force_login(viewer)
        restricted = self.page(search="Uniform")
        self.assertEqual(restricted.status_code, 200)
        self.assertEqual([link["title"] for link in ActionLinks(restricted.content).links], ["View Details"] * 3)
        row = restricted.context["inventory_page"][0]
        detail = self.client.get(row["inventory_url"])
        self.assertNotContains(detail, 'id="inventory-movements"')
        self.assertNotEqual(self.client.get(row["details_url"]).status_code, 200)

        viewer.user_permissions.add(Permission.objects.get(content_type__app_label="accounts", codename="can_view_stock_movements"))
        self.client.force_login(viewer)
        movements = self.page(search="Uniform")
        self.assertEqual([link["title"] for link in ActionLinks(movements.content).links], ["View Details", "Stock Movements"] * 3)
        self.assertContains(self.client.get(movements.context["inventory_page"][0]["movements_url"]), 'id="inventory-movements"')

    def test_inventory_thumbnails_use_exact_variant_then_product_and_preserve_stock(self):
        import base64
        from copy import deepcopy
        image = Path(__file__).resolve().parents[3] / 'static/assets/img/icon.png'
        parent = 'data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode()
        self.product.image_url = json.dumps([parent, '/media/unused-gallery-image.png'])
        self.product.customization_options[0]['options'][2]['image'] = '/media/large-only-photo.png'
        self.product.save(update_fields=['image_url','customization_options'])
        before = deepcopy(self.product.customization_options)
        response = self.page(product_id=self.product.pk)
        rows = {row['name']:row for row in response.context['inventory_page']}
        primary = reverse('product_image', args=[self.product.pk])
        self.assertEqual(rows['Small']['thumbnail_url'], primary)
        self.assertEqual(rows['Medium']['thumbnail_url'], primary)
        self.assertEqual(rows['Large']['thumbnail_url'], '/media/large-only-photo.png')
        self.assertEqual(rows['Large']['thumbnail_fallback_url'], primary)
        self.assertEqual(rows['Small']['thumbnail_fallback_url'], '')
        self.assertContains(response, 'id="inventoryFilterHeading">Filters</h3>')
        self.assertContains(response, 'aria-labelledby="inventoryFilterHeading"')
        self.assertContains(response, 'loading="lazy"', count=3)
        self.assertEqual(self.client.get(primary).status_code, 200)
        self.product.refresh_from_db();self.assertEqual(self.product.customization_options, before)
        self.assertEqual([(rows[n]['available'],rows[n]['threshold']) for n in ('Small','Medium','Large')],[(10,3),(5,2),(1,2)])
        blank = self.page(product_id=self.zero.pk)
        self.assertEqual(blank.context['inventory_page'][0]['thumbnail_url'], '')
        self.assertContains(blank, 'inventory-thumbnail-placeholder')

    def test_filter_apply_reset_and_detail_links_preserve_tab_authorization(self):
        from accounts.admin_tab_auth import create_admin_tab_token
        token = create_admin_tab_token(self.admin)
        response = self.page(__at=token, category="Clothing")
        self.assertContains(response, f'name="__at" value="{token}"')
        reset = parse_qs(urlparse(response.context["inventory_reset_url"]).query)
        self.assertEqual(reset, {"view":["inventory"], "__at":[token]})
        row = response.context["inventory_page"][0]
        self.assertEqual(parse_qs(urlparse(row["inventory_url"]).query)["__at"], [token])
        self.assertEqual(parse_qs(urlparse(row["details_url"]).query)["__at"], [token])

    def test_stock_and_audit_roll_back_together(self):
        sku = self.product.inventory_skus.get(variant_name="Large")
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                self.product.customization_options[0]["options"][2]["stock"] = 7
                self.product.save(update_fields=["customization_options", "updated_at"])
                raise RuntimeError("Abort isolated test transaction")
        self.product.refresh_from_db()
        self.assertEqual(self.product.customization_options[0]["options"][2]["stock"], 1)
        self.assertFalse(sku.movements.filter(kind="adjustment").exists())

    def test_partial_save_does_not_record_unsaved_variant_changes(self):
        sku = self.product.inventory_skus.get(variant_name="Large")
        self.product.customization_options[0]["options"][2]["stock"] = 9
        self.product.stock = 24
        self.product.save(update_fields=["stock", "updated_at"])
        self.product.refresh_from_db()
        self.assertEqual(self.product.customization_options[0]["options"][2]["stock"], 1)
        self.assertFalse(sku.movements.filter(kind="adjustment").exists())

    def test_retired_variant_orders_keep_their_original_stock_identity(self):
        from django.utils import timezone
        from .services.inventory_records import record_completed_sale
        old_sku = self.product.inventory_skus.get(variant_name="Small")
        old_sku.movements.all().delete()  # A real legacy order without an audit ledger.
        order = MarketplaceOrder.objects.create(product=self.product, product_name=self.product.name,
            quantity=2, unit_price=250, total_price=500, inventory_deducted=True,
            status=MarketplaceOrder.STATUS_COMPLETED, completed_at=timezone.now(),
            customization={"selections":[{"group":"Size", "option":"Small"}]})
        self.product.customization_options = []
        self.product.customization_enabled = False
        self.product.stock = 20
        self.product.save()
        retired = self.page(inventory_item=old_sku.pk).context["inventory_detail"]
        self.assertIsNone(retired["available"])
        self.assertEqual({event["kind"] for event in retired["movements"]}, {"Reservation", "Sale"})
        parent = self.product.inventory_skus.get(variant_name="")
        parent_detail = self.page(inventory_item=parent.pk).context["inventory_detail"]
        self.assertFalse(any(event["reference"].startswith("Order #") for event in parent_detail["movements"]))
        record_completed_sale(order, self.admin.username)
        self.assertEqual(old_sku.movements.get(kind="sale", order=order).quantity_change, -2)
        self.assertFalse(parent.movements.filter(order=order).exists())


class InventorySKUMigrationTests(TransactionTestCase):
    # Scope test-only cleanup and allow cascading legacy FK references in keepdb.
    available_apps = ["accounts", "api", "django.contrib.auth", "django.contrib.contenttypes"]

    def test_existing_inventory_gets_skus_without_quantity_changes_or_fake_history(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("api", "0032_product_component_bundles")])
        try:
            old = executor.loader.project_state([("api", "0032_product_component_bundles")]).apps
            OldUser, OldProduct = old.get_model("accounts", "User"), old.get_model("api", "Product")
            with connection.cursor() as cursor:
                columns = {row.name for row in connection.introspection.get_table_description(cursor, "campushub_accounts_user")}
                if "email_verified" in columns:
                    cursor.execute('ALTER TABLE campushub_accounts_user ALTER COLUMN email_verified SET DEFAULT FALSE')
            user = OldUser.objects.create(username="pre-sku-owner")
            product = OldProduct.objects.create(seller_id=user.pk, name="Uniform", price=250, stock=15,
                product_code="PRD-0041", customization_options=[{"name":"Size", "options":[
                    {"name":"Small", "stock":10}, {"name":"Medium", "stock":5}, {"name":"Untracked"}]}])
            bundle = OldProduct.objects.create(seller_id=user.pk, name="Meal", price=100, stock=0, product_type="bundle")
            before = list(OldProduct.objects.order_by("pk").values("pk", "stock", "customization_options", "product_code"))
            executor = MigrationExecutor(connection)
            executor.migrate([("api", "0033_inventory_sku_and_movements")])
            self.assertEqual(list(Product.objects.order_by("pk").values("pk", "stock", "customization_options", "product_code")), before)
            self.assertEqual(InventorySKU.objects.filter(product_id=product.pk).count(), 3)
            self.assertFalse(InventorySKU.objects.filter(variant_name="Untracked").exists())
            self.assertTrue(InventorySKU.objects.get(product_id=bundle.pk).code.startswith("BND-"))
            self.assertFalse(InventoryStockMovement.objects.exists())
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
