"""Real PostgreSQL records; never used to seed the working database."""
import json
import os
from pathlib import Path
from uuid import uuid4

from django.test import TestCase, override_settings
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from accounts.models import Department, User
from api.models import (Product, MarketplaceOrder, BundleComponent, InventoryBatch,
    InventoryBatchAllocation, InventoryFIFOControl, InventoryOperation, InventoryStockMovement)
from .services import fifo


@override_settings(CAMPUSHUB_FIFO_ENABLED=True, PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FIFOInventoryTests(TestCase):
    def setUp(self):
        self.program, _ = Department.objects.get_or_create(code="BSIT", defaults={"name": "Information Technology", "is_program": True})
        self.admin = User.objects.create_superuser(username="fifo-admin", role="Super Admin", department=self.program)
        self.product = Product.objects.create(seller=self.admin, name="FIFO test item", price="10.00", stock=0,
            low_stock_threshold=0, category="Supplies", approval_status="approved")
        self.sku = self.product.inventory_skus.get(group_name="", variant_name="")
        fifo.initialize(fifo.reconciliation()["fingerprint"])
        self.client.force_login(self.admin)

    def receive(self, qty, *, sku=None, key=None):
        return fifo.receive((sku or self.sku).pk, qty, "Actual isolated test receipt", self.admin, key or uuid4())

    def order(self, qty, *, product=None, selections=None, key=None):
        headers = {"HTTP_IDEMPOTENCY_KEY": str(key)} if key else {}
        return self.client.post(reverse("marketplace_orders"), json.dumps({"product_id": (product or self.product).pk,
            "buyer_user_id": self.admin.pk, "quantity": qty, "customization": selections or []}), content_type="application/json", **headers)

    def cancel(self, order):
        return self.client.post(reverse("admin_order_update", args=[order.pk]), json.dumps({"status": "cancelled", "cancellation_reason": "Isolated FIFO verification"}), content_type="application/json")

    def test_demonstration_fifo_order_and_exact_cancellation(self):
        self.receive(20); self.receive(30)
        batches = list(self.sku.batches.order_by("pk"))
        response = self.order(25)
        self.assertEqual(response.status_code, 201, response.content)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(list(order.fifo_allocations.order_by("batch_id").values_list("quantity", flat=True)), [20, 5])
        self.assertEqual(list(self.sku.batches.order_by("pk").values_list("remaining_quantity", flat=True)), [0, 25])
        self.assertEqual(self.cancel(order).status_code, 200)
        self.assertEqual(self.cancel(order).status_code, 200)
        self.assertEqual(list(self.sku.batches.order_by("pk").values_list("remaining_quantity", flat=True)), [20, 30])
        self.assertEqual(InventoryBatchAllocation.objects.filter(state="released").count(), 2)
        self.product.refresh_from_db(); self.assertEqual(self.product.stock, 50)
        self.assertEqual([b.pk for b in batches], list(self.sku.batches.order_by("pk").values_list("pk", flat=True)))

    def test_completion_does_not_deduct_again(self):
        self.receive(50)
        response = self.order(25); self.assertEqual(response.status_code, 201)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        for status in ("processing", "ready_for_pickup", "completed", "completed"):
            response = self.client.post(reverse("admin_order_update", args=[order.pk]), json.dumps({"status": status,
                "payment_status": "paid", "pickup_confirmed": True}), content_type="application/json")
            self.assertEqual(response.status_code, 200, response.content)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 25)
        self.assertEqual(self.sku.batches.get().remaining_quantity, 25)
        self.assertEqual(list(order.fifo_allocations.values_list("state", flat=True)), ["consumed"])
        self.assertEqual(order.inventory_movements.filter(kind="sale").count(), 1)

    def test_insufficient_stock_and_reconciliation_mismatch_roll_back(self):
        self.receive(20)
        before = InventoryStockMovement.objects.count()
        self.assertEqual(self.order(21).status_code, 409)
        self.assertFalse(MarketplaceOrder.objects.exists())
        self.assertEqual(InventoryStockMovement.objects.count(), before)
        InventoryBatch.objects.update(remaining_quantity=19)
        self.assertEqual(self.order(2).status_code, 409)
        self.product.refresh_from_db(); self.assertEqual(self.product.stock, 20)
        self.assertFalse(InventoryBatchAllocation.objects.exists())

    def test_receipt_retry_and_keyed_order_retry(self):
        key = uuid4()
        first = self.receive(50, key=key)
        self.assertEqual(self.receive(50, key=key), first)
        with self.assertRaises(fifo.FIFOError): self.receive(51, key=key)
        self.assertEqual(self.sku.batches.count(), 1)
        order_key = uuid4()
        first_order = self.order(25, key=order_key)
        self.assertEqual(first_order.status_code, 201)
        self.assertEqual(self.order(25, key=order_key).json(), first_order.json())
        self.assertEqual(self.order(26, key=order_key).status_code, 409)
        self.assertEqual(MarketplaceOrder.objects.count(), 1)
        self.assertEqual(self.sku.batches.get().remaining_quantity, 25)

    def test_variant_batches_use_stable_skus_and_survive_reordering(self):
        product = Product.objects.create(seller=self.admin, name="Sizes", price=10, stock=0, approval_status="approved",
            customization_enabled=True, customization_options=[{"name": "Size", "required": True, "selection": "single", "options": [
                {"name": "Small", "stock": 0, "low_stock_threshold": 0}, {"name": "Large", "stock": 0, "low_stock_threshold": 0}]}])
        small = product.inventory_skus.get(variant_name="Small"); large = product.inventory_skus.get(variant_name="Large")
        self.receive(20, sku=small); self.receive(30, sku=large)
        product.refresh_from_db(); product.customization_options[0]["options"].reverse(); product.save()
        response = self.order(5, product=product, selections=[{"group": "Size", "option": "Small"}])
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(small.batches.get().remaining_quantity, 15); self.assertEqual(large.batches.get().remaining_quantity, 30)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(self.cancel(order).status_code, 200)
        self.assertEqual(small.batches.get().remaining_quantity, 20)

    def test_bundle_components_and_changed_recipe_restore_recorded_batches(self):
        self.receive(20); self.receive(30)
        other = Product.objects.create(seller=self.admin, name="Other component", price=2, stock=100, approval_status="approved")
        bundle = Product.objects.create(seller=self.admin, name="Bundle", price=15, stock=0, product_type="bundle", approval_status="approved")
        BundleComponent.objects.create(bundle=bundle, product=self.product, required_quantity=2)
        component = BundleComponent.objects.create(bundle=bundle, product=other, required_quantity=1)
        response = self.order(15, product=bundle); self.assertEqual(response.status_code, 201, response.content)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(list(order.fifo_allocations.filter(batch__sku=self.sku).order_by("batch_id").values_list("quantity", flat=True)), [20, 10])
        component.required_quantity = 4; component.save()
        self.assertEqual(self.cancel(order).status_code, 200)
        other.refresh_from_db(); self.assertEqual(other.stock, 100)
        self.assertFalse(bundle.inventory_skus.get(variant_name="").batches.exists())

    def test_stock_edits_and_removed_variants_are_audited_corrections(self):
        self.receive(20)
        response = self.client.post(reverse("admin_update_product_stock", args=[self.product.pk]), json.dumps({"stock": 25}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(list(self.sku.batches.order_by("pk").values_list("origin", flat=True)), ["receipt", "adjustment"])
        self.product.refresh_from_db(); self.product.stock = 10; self.product.save(update_fields=["stock"])
        self.assertEqual(sum(self.sku.batches.values_list("remaining_quantity", flat=True)), 10)
        self.assertEqual(InventoryBatchAllocation.objects.filter(state="adjustment").aggregate(total=Sum('quantity'))['total'], 15)
        if os.environ.get("FIFO_REVIEW_DIR"):
            page = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo"})
            (Path(os.environ["FIFO_REVIEW_DIR"])/"adjustment.html").write_bytes(page.content)
        with self.assertRaises(fifo.FIFOError): Product.objects.filter(pk=self.product.pk).update(stock=99)
        self.product.stock = 99
        with self.assertRaises(fifo.FIFOError): Product.objects.bulk_update([self.product], ["stock"])
        with self.assertRaises(fifo.FIFOError): Product.objects.bulk_create([Product(seller=self.admin, name="Bypass", price=1, stock=1)])

    def test_legacy_opening_preserves_available_and_active_hold(self):
        InventoryFIFOControl.objects.update(active=False)
        self.product.stock = 50; self.product.save()
        response = self.order(5); self.assertEqual(response.status_code, 201)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        before = fifo.reconciliation(); line = next(row for row in before["rows"] if row["sku"] == self.sku.pk)
        self.assertEqual((line["available"], line["reserved"], line["opening_quantity"]), (45, 5, 50))
        fifo.initialize(before["fingerprint"])
        batch = self.sku.batches.get()
        self.assertEqual((batch.origin, batch.received_at, batch.initial_quantity, batch.remaining_quantity), ("opening", None, 50, 45))
        self.assertTrue(order.fifo_allocations.get().legacy)
        page = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_section": "fifo"})
        self.assertContains(page, "<dt>Batch Type</dt><dd>Starting Stock</dd>")
        self.assertContains(page, "Not recorded<small>Recorded")
        self.assertContains(page, "Existing reservation at starting stock")
        self.assertContains(page, "<dt>Recorded By</dt><dd>—</dd>")
        projected = next(row for row in page.context["fifo_batches"] if row.pk == batch.pk)
        self.assertEqual((projected.remaining_quantity, projected.reserved_quantity), (45, 5))
        self.assertIsNone(projected.received_at)
        movements = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"movements"})
        reconciled = next(row for row in movements.context["fifo_movements"] if row.kind == "reservation")
        self.assertTrue(reconciled.allocation_reconciled)
        self.assertEqual([a.quantity for a in reconciled.display_allocations], [5])
        self.assertContains(movements, "Opening Balance Reconciliation")
        self.assertContains(movements, 'title="View Allocation"', count=1)
        self.assertIsNone(order.fifo_allocations.get().movement_id)
        if os.environ.get("FIFO_REVIEW_DIR"):
            (Path(os.environ["FIFO_REVIEW_DIR"]) / "opening.html").write_bytes(page.content)
            (Path(os.environ["FIFO_REVIEW_DIR"]) / "legacy-movements.html").write_bytes(movements.content)
        self.assertEqual(self.cancel(order).status_code, 200)
        batch.refresh_from_db(); self.assertEqual(batch.remaining_quantity, 50)

    def test_cutover_mismatch_repeat_and_unverified_backup_are_blocked(self):
        with self.assertRaises(fifo.FIFOError): fifo.initialize(fifo.reconciliation()["fingerprint"])
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError): call_command("initialize_fifo_inventory", apply=True)

    def test_permissions_scope_csrf_and_receiving_validation(self):
        self.receive(10)
        viewer = User.objects.create_user(username="fifo-viewer", is_staff=True, department=self.program)
        from django.contrib.auth.models import Permission
        viewer.user_permissions.add(Permission.objects.get(codename="can_view_inventory", content_type__app_label="accounts"))
        self.client.force_login(viewer)
        self.assertEqual(self.client.post(reverse("admin_receive_stock"), '{}', content_type="application/json").status_code, 403)
        self.assertNotContains(self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_section": "fifo"}), 'id="fifoReceiveForm"')
        for value in (0, -1, "1.5", True, 2147483648):
            with self.assertRaises(fifo.FIFOError): self.receive(value)
        from django.test import Client
        protected = Client(enforce_csrf_checks=True); protected.force_login(self.admin)
        self.assertEqual(protected.post(reverse("admin_receive_stock"), '{}', content_type="application/json").status_code, 403)

    def test_expiry_preserved_and_no_fifo_queries_when_disabled(self):
        from datetime import timedelta
        self.receive(20)
        self.product.refresh_from_db()
        self.product.category = "Snacks"; self.product.expiry_date = timezone.localdate() - timedelta(days=1); self.product.save()
        response = self.order(1)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Expired", response.json()["error"])
        self.assertEqual(self.sku.batches.get().remaining_quantity, 20)
        with override_settings(CAMPUSHUB_FIFO_ENABLED=False):
            with self.assertNumQueries(0): self.assertFalse(fifo.enabled())

    def test_inventory_views_and_export_isolated_ui_fixtures(self):
        receipt = self.receive(20); self.receive(30)
        response = self.order(25); self.assertEqual(response.status_code, 201)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        directory = os.environ.get("FIFO_REVIEW_DIR")
        for section in ("overview", "fifo", "movements"):
            page = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_section": section})
            self.assertEqual(page.status_code, 200)
            if section == "overview": self.assertContains(page, 'title="Stock Movements"')
            self.assertEqual([tab["label"] for tab in page.context["inventory_tabs"]], ["Stock Overview", "Stock Movements", "Stock Batches"])
            self.assertNotContains(page, "FIFO Batches")
            self.assertNotContains(page, "FIFO Allocations")
            if section == "fifo":
                self.assertContains(page, "Available Quantity")
                self.assertContains(page, "Reserved Quantity")
                self.assertContains(page, 'aria-label="Stock Receiving"')
                self.assertContains(page, 'id="fifoReceiveForm"')
            else:
                self.assertNotContains(page, 'id="fifoReceiveForm"')
            if section == "movements": self.assertContains(page, "Batch Allocation Details")
            if directory:
                root = Path(directory); root.mkdir(parents=True, exist_ok=True)
                (root / f"{section}.html").write_bytes(page.content)
                (root / "ids.json").write_text(json.dumps({"sku": self.sku.pk, "order": order.pk}), encoding="utf-8")
                (root / "received.json").write_text(json.dumps(receipt), encoding="utf-8")
        detail = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_item": self.sku.pk})
        self.assertContains(detail, "Batch Allocation Details")
        self.assertNotContains(detail, "FIFO allocations")
        if directory:
            (Path(directory) / "detail.html").write_bytes(detail.content)

    def test_batch_display_separates_reserved_consumed_and_released_quantities(self):
        self.receive(20); self.receive(30)
        response = self.order(25); self.assertEqual(response.status_code, 201)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])

        def page_rows():
            page = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_section": "fifo"})
            self.assertEqual(page.status_code, 200)
            return page, [(b.remaining_quantity, b.reserved_quantity, b.status_label) for b in page.context["fifo_batches"]]

        page, rows = page_rows()
        self.assertEqual(rows, [(0, 20, "Fully reserved"), (25, 5, "Partially reserved")])
        for status in ("processing", "ready_for_pickup", "completed"):
            updated = self.client.post(reverse("admin_order_update", args=[order.pk]), json.dumps({
                "status": status, "payment_status": "paid", "pickup_confirmed": True}), content_type="application/json")
            self.assertEqual(updated.status_code, 200, updated.content)
        page, rows = page_rows()
        self.assertEqual(rows, [(0, 0, "Depleted"), (25, 0, "Available")])
        self.assertEqual([b.consumed_quantity for b in page.context["fifo_batches"]], [20, 5])
        self.assertContains(page, "Consumed")
        self.assertNotContains(page, "Fully reserved")
        if os.environ.get("FIFO_REVIEW_DIR"):
            (Path(os.environ["FIFO_REVIEW_DIR"]) / "consumed.html").write_bytes(page.content)
            movements = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"movements"})
            (Path(os.environ["FIFO_REVIEW_DIR"]) / "consumed-movements.html").write_bytes(movements.content)
        second = self.order(10); self.assertEqual(second.status_code, 201)
        self.assertEqual(page_rows()[1], [(0, 0, "Depleted"), (15, 10, "Partially reserved")])
        self.assertEqual(self.cancel(MarketplaceOrder.objects.get(pk=second.json()["order"]["id"])).status_code, 200)
        page, rows = page_rows()
        self.assertEqual(rows, [(0, 0, "Depleted"), (25, 0, "Available")])
        self.assertContains(page, "Released")
        if os.environ.get("FIFO_REVIEW_DIR"):
            movements = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"movements"})
            (Path(os.environ["FIFO_REVIEW_DIR"]) / "released-movements.html").write_bytes(movements.content)
        self.product.refresh_from_db(); self.assertEqual(self.product.stock, 25)

    def test_drawer_content_uses_real_records_and_omits_empty_movement_actions(self):
        self.receive(20); self.receive(30)
        response = self.order(25); self.assertEqual(response.status_code, 201)
        page = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"movements"})
        self.assertContains(page, 'id="inventoryDetailsDrawer"', count=1)
        self.assertNotContains(page, '<details class="fifo-allocation-details">')
        allocations = []
        for movement in page.context["fifo_movements"]:
            marker = f'data-inventory-detail="inventoryMovementDetail{movement.pk}"'
            if movement.display_allocations:
                self.assertContains(page, marker)
                allocations.extend(movement.display_allocations)
            else:
                self.assertNotContains(page, marker)
                self.assertNotContains(page, f'<template id="inventoryMovementDetail{movement.pk}">')
        self.assertEqual(sorted(a.quantity for a in allocations), [5, 20])
        self.assertContains(page, 'title="View Allocation"', count=1)
        batch_page = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo"})
        self.assertContains(batch_page, "Seller / Owner")
        self.assertContains(batch_page, "Actual isolated test receipt")
        for batch in batch_page.context["fifo_batches"]:
            self.assertContains(batch_page, f'<template id="inventoryBatchDetail{batch.pk}">')
            self.assertEqual(batch.consumed_quantity, 0)
            self.assertEqual(batch.owner_label, self.admin.username)
        self.product.name = '<script>alert("inventory")</script>'
        self.product.save(update_fields=["name"])
        escaped = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo"})
        self.assertNotContains(escaped, '<script>alert("inventory")</script>')
        self.assertContains(escaped, '&lt;script&gt;')

    def test_drawer_templates_preserve_scope_and_movement_permissions(self):
        from django.contrib.auth.models import Permission
        from accounts.role_permissions import sync_user_admin_permissions
        self.receive(20)
        order = self.order(2); self.assertEqual(order.status_code, 201)
        reference = order.json()["order"]["order_code"]
        own_batch = self.sku.batches.get()
        viewer = User.objects.create_user(username="drawer-reader", is_staff=True, department=self.program)
        viewer.user_permissions.add(Permission.objects.get(codename="can_view_inventory", content_type__app_label="accounts"))
        self.client.force_login(viewer)
        page = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo"})
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "Related Transactions")
        self.assertNotContains(page, reference)
        self.assertNotContains(page, 'id="fifoReceiveForm"')
        directory = os.environ.get("FIFO_REVIEW_DIR")
        if directory: (Path(directory)/"viewer.html").write_bytes(page.content)
        other, _ = Department.objects.get_or_create(code="BFPT",defaults={"name":"Food Processing", "is_program":True})
        manager = User.objects.create_user(username="drawer-manager",is_staff=True,role="Marketplace Admin",department=other)
        sync_user_admin_permissions(manager)
        product = Product.objects.create(seller=manager,name="Authorized other product",price=10,stock=0,approval_status="approved")
        sku = product.inventory_skus.get(variant_name="")
        self.receive(7,sku=sku)
        self.client.force_login(manager)
        page = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo"})
        self.assertContains(page, product.name)
        self.assertNotContains(page, own_batch.code)
        self.assertNotContains(page, f'inventoryBatchDetail{own_batch.pk}')
        self.assertNotContains(page, reference)
        tampered = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo", "product_id":self.product.pk})
        self.assertNotContains(tampered, f'inventoryBatchDetail{own_batch.pk}')
        self.assertNotContains(tampered, reference)
        searched = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo", "search":own_batch.code})
        self.assertEqual(searched.context["fifo_batches"].paginator.count, 0)
        self.assertNotContains(searched, f'inventoryBatchDetail{own_batch.pk}')

    def test_batch_reference_search_intersects_metadata_without_showing_sibling_batches(self):
        from accounts.models import ProgramMajor
        major = ProgramMajor.objects.create(program=self.program, code="BATCH", name="Batch search major")
        self.product.department = self.program; self.product.major = major
        self.product.save(update_fields=["department", "major"])
        self.receive(20); self.receive(30)
        first, selected = self.sku.batches.order_by("pk")
        other = Product.objects.create(seller=self.admin, name="Unrelated stock", price=2, stock=0, approval_status="approved")
        self.receive(7, sku=other.inventory_skus.get(variant_name=""))
        params = {"view":"inventory", "inventory_section":"fifo", "search":selected.code.lower(),
                  "program":self.program.pk, "major":major.pk, "seller":self.admin.pk,
                  "category":"Supplies", "inventory_status":"in_stock"}
        page = self.client.get(reverse("admin_products_page"), params)
        self.assertEqual([batch.pk for batch in page.context["fifo_batches"]], [selected.pk])
        self.assertEqual([row["sku_id"] for row in page.context["inventory_page"]], [self.sku.pk])
        self.assertEqual([row["sku_id"] for row in page.context["fifo_receivable"]], [self.sku.pk])
        self.assertNotContains(page, f'<template id="inventoryBatchDetail{first.pk}">')
        for key, value in {"program":"999999", "major":"999999", "seller":"999999", "category":"Other", "inventory_status":"low_stock"}.items():
            mismatch = self.client.get(reverse("admin_products_page"), {**params, key:value})
            self.assertEqual(mismatch.context["fifo_batches"].paginator.count, 0)
        partial = self.client.get(reverse("admin_products_page"), {**params, "search":"bat-"})
        self.assertEqual([batch.pk for batch in partial.context["fifo_batches"]], [first.pk, selected.pk])
        self.assertContains(page, "<dt>Recorded By</dt><dd>fifo-admin</dd>")
        if os.environ.get("FIFO_REVIEW_DIR"):
            (Path(os.environ["FIFO_REVIEW_DIR"])/"batch-search.html").write_bytes(page.content)

    def test_batch_search_supports_variant_sku_product_and_actual_seller(self):
        seller = User.objects.create_user(username="batch-owner", first_name="Actual", last_name="Owner")
        product = Product.objects.create(seller=seller, name="Grouped inventory", price=4, stock=0,
            approval_status="approved", customization_enabled=True, customization_options=[{
                "name":"Color", "selection":"single", "required":True,
                "options":[{"name":"Crimson", "stock":0}, {"name":"Azure", "stock":0}]}])
        skus = {sku.variant_name:sku for sku in product.inventory_skus.exclude(variant_name="")}
        for sku in skus.values(): self.receive(6, sku=sku)
        for search, expected in (("Crimson", {skus["Crimson"].pk}), (skus["Azure"].code, {skus["Azure"].pk}),
                                 ("Grouped inventory", {sku.pk for sku in skus.values()}),
                                 ("Actual Owner", {sku.pk for sku in skus.values()})):
            page = self.client.get(reverse("admin_products_page"), {"view":"inventory", "inventory_section":"fifo", "search":search})
            self.assertEqual({batch.sku_id for batch in page.context["fifo_batches"]}, expected)

    def test_drawer_templates_only_include_current_filtered_batch_page(self):
        from accounts.models import ProgramMajor
        from urllib.parse import parse_qs
        major = ProgramMajor.objects.create(program=self.program, code="PAGE", name="Batch page major")
        self.product.department = self.program; self.product.major = major
        self.product.save(update_fields=["department", "major"])
        for _ in range(31): self.receive(1)
        params = {"view":"inventory", "inventory_section":"fifo", "search":"FIFO", "program":self.program.pk,
                  "major":major.pk, "seller":self.admin.pk, "category":"Supplies", "inventory_status":"in_stock"}
        for number in (1, 2):
            page = self.client.get(reverse("admin_products_page"), {**params, "fifo_page":number})
            self.assertEqual(page.context["fifo_batches"].paginator.count, 31)
            self.assertEqual(len(page.context["fifo_batches"]), 30 if number == 1 else 1)
            self.assertContains(page, 'aria-label="Stock batch pages"', count=1)
            self.assertContains(page, 'aria-label="Previous page"', count=1)
            self.assertContains(page, 'aria-label="Next page"', count=1)
            disabled = "Previous page" if number == 1 else "Next page"
            self.assertContains(page, f'class="inventory-page-step" aria-label="{disabled}" title="{disabled}" disabled')
            for key, value in params.items(): self.assertEqual(parse_qs(page.context["fifo_page_query"])[key], [str(value)])
            if os.environ.get("FIFO_REVIEW_DIR"):
                (Path(os.environ["FIFO_REVIEW_DIR"])/f"batch-page{number}.html").write_bytes(page.content)
        self.assertEqual(page.context["fifo_batches"].number, 2)
        self.assertEqual(len(page.context["fifo_batches"]), 1)
        batch = page.context["fifo_batches"][0]
        self.assertContains(page, 'data-inventory-detail="inventoryBatchDetail', count=1)
        self.assertContains(page, f'<template id="inventoryBatchDetail{batch.pk}">')
        first = self.sku.batches.order_by("pk").first()
        self.assertNotContains(page, f'<template id="inventoryBatchDetail{first.pk}">')
        self.assertIn("search=FIFO", page.context["fifo_page_query"])
        self.assertIn("inventory_section=fifo", page.context["fifo_page_query"])
        if os.environ.get("FIFO_REVIEW_DIR"):
            (Path(os.environ["FIFO_REVIEW_DIR"])/"paginated.html").write_bytes(page.content)

    def test_movement_pagination_preserves_filters_and_bounds_server_page(self):
        from urllib.parse import parse_qs
        from accounts.models import ProgramMajor
        major = ProgramMajor.objects.create(program=self.program,code="MOV",name="Movement test major")
        self.product.department=self.program;self.product.major=major
        self.product.save(update_fields=["department","major"])
        for _ in range(31): self.receive(1)
        params = {"view":"inventory", "inventory_section":"movements", "search":"FIFO", "program":self.program.pk,
                  "major":major.pk,"seller":self.admin.pk, "category":"Supplies", "inventory_status":"in_stock",
                  "product_id":self.product.pk}
        before = (self.sku.batches.count(), InventoryStockMovement.objects.count(), sum(self.sku.batches.values_list("remaining_quantity",flat=True)))
        for number in (1, 2):
            page = self.client.get(reverse("admin_products_page"), {**params,"fifo_page":number})
            self.assertEqual(page.status_code,200)
            movements = page.context["fifo_movements"]
            self.assertEqual(movements.number,number)
            self.assertEqual(movements.paginator.count,32)
            self.assertEqual(len(movements),30 if number==1 else 2)
            self.assertContains(page, 'aria-label="Stock movement pages"',count=1)
            self.assertContains(page, 'aria-label="Previous page"',count=1)
            self.assertContains(page, 'aria-label="Next page"',count=1)
            self.assertContains(page, 'class="inventory-page-step" aria-label="'+('Previous page' if number==1 else 'Next page')+'" title="'+('Previous page' if number==1 else 'Next page')+'" disabled')
            query = parse_qs(page.context["fifo_page_query"])
            for key,value in params.items(): self.assertEqual(query[key],[str(value)])
            self.assertFalse(any(m.display_allocations for m in movements))
            self.assertContains(page, '+1')
            if os.environ.get("FIFO_REVIEW_DIR"):
                (Path(os.environ["FIFO_REVIEW_DIR"])/f"movement-page{number}.html").write_bytes(page.content)
        self.assertEqual(before,(self.sku.batches.count(),InventoryStockMovement.objects.count(),sum(self.sku.batches.values_list("remaining_quantity",flat=True))))

    def test_movement_quantity_direction_and_recorded_actor_are_presentational(self):
        self.receive(10)
        response = self.order(2); self.assertEqual(response.status_code,201)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        self.assertEqual(self.cancel(order).status_code,200)
        page = self.client.get(reverse("admin_products_page"),{"view":"inventory","inventory_section":"movements"})
        kinds = {m.kind:m for m in page.context["fifo_movements"]}
        self.assertEqual((kinds['receipt'].quantity_change,kinds['reservation'].quantity_change,kinds['release'].quantity_change),(10,-2,2))
        self.assertContains(page,'+10');self.assertContains(page,'-2');self.assertContains(page,'+2')
        self.assertEqual(kinds['receipt'].actor,self.admin.username)
        self.assertEqual(kinds['opening'].actor,'')
        self.assertContains(page,'<td>—</td>')
        self.assertFalse(any(m.allocation_reconciled for m in kinds.values()))
        if os.environ.get("FIFO_REVIEW_DIR"):
            (Path(os.environ["FIFO_REVIEW_DIR"])/"movement-directions.html").write_bytes(page.content)

    def test_legacy_reconciliation_display_requires_matching_order_and_sku(self):
        InventoryFIFOControl.objects.update(active=False)
        self.product.stock=10;self.product.save()
        response=self.order(2);self.assertEqual(response.status_code,201)
        order=MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        other=Product.objects.create(seller=self.admin,name="Unrelated inventory",price=2,stock=4,approval_status="approved")
        fifo.initialize(fifo.reconciliation()['fingerprint'])
        other.stock=3;other.save(update_fields=['stock'])
        page=self.client.get(reverse('admin_products_page'),{'view':'inventory','inventory_section':'movements'})
        matching=[m for m in page.context['fifo_movements'] if m.allocation_reconciled]
        self.assertEqual(len(matching),1)
        self.assertEqual((matching[0].order_id,matching[0].sku_id),(order.pk,self.sku.pk))
        legacy=order.fifo_allocations.get()
        self.assertIsNone(legacy.movement_id)
        legacy.legacy=False;legacy.save(update_fields=['legacy'])
        page=self.client.get(reverse('admin_products_page'),{'view':'inventory','inventory_section':'movements'})
        reserved=next(m for m in page.context['fifo_movements'] if m.kind=='reservation')
        self.assertFalse(reserved.display_allocations)
        self.assertFalse(reserved.allocation_reconciled)

    def test_batch_empty_and_inactive_views_keep_honest_labels(self):
        page = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_section": "fifo"})
        self.assertContains(page, 'colspan="8"')
        self.assertContains(page, "No inventory batches match the selected filters.")
        if os.environ.get("FIFO_REVIEW_DIR"):
            (Path(os.environ["FIFO_REVIEW_DIR"]) / "empty.html").write_bytes(page.content)
        with override_settings(CAMPUSHUB_FIFO_ENABLED=False):
            for section in ("fifo", "movements"):
                page = self.client.get(reverse("admin_products_page"), {"view": "inventory", "inventory_section": section})
                self.assertContains(page, "Stock receiving is not available yet.")
                self.assertNotContains(page, 'id="fifoReceiveForm"')
                self.assertNotContains(page, "FIFO receiving")
                if section == "fifo" and os.environ.get("FIFO_REVIEW_DIR"):
                    (Path(os.environ["FIFO_REVIEW_DIR"]) / "inactive.html").write_bytes(page.content)
            with self.assertRaisesRegex(fifo.FIFOError, "Stock receiving is not available yet"):
                self.receive(1)

    def test_receiving_endpoint_replays_and_foreign_scope_is_blocked(self):
        data = {"sku": self.sku.pk, "quantity": 10, "reference": "Endpoint test receipt", "key": str(uuid4())}
        first = self.client.post(reverse("admin_receive_stock"), json.dumps(data), content_type="application/json")
        self.assertEqual(first.status_code, 200, first.content)
        self.assertEqual(self.client.post(reverse("admin_receive_stock"), json.dumps(data), content_type="application/json").json(), first.json())
        self.assertEqual(self.sku.batches.count(), 1)
        from accounts.role_permissions import sync_user_admin_permissions
        other_program, _ = Department.objects.get_or_create(code="BFPT", defaults={"name": "Food Processing", "is_program": True})
        manager = User.objects.create_user(username="fifo-other-scope", department=other_program, role="Marketplace Admin", is_staff=True)
        sync_user_admin_permissions(manager)
        with self.assertRaises(fifo.FIFOError): fifo.receive(self.sku.pk, 10, "Outside scope", manager, uuid4())

    def test_shared_variant_bundle_pools_and_retired_variant_guard(self):
        product = Product.objects.create(seller=self.admin, name="Shared options", price=10, stock=0, approval_status="approved", customization_enabled=True,
            customization_options=[{"name":"Size", "required":True, "options":[{"name":"Large", "stock":5}]},
                {"name":"Flavor", "required":True, "options":[{"name":"Vanilla", "stock":10}, {"name":"Chocolate", "stock":10}]}])
        bundle = Product.objects.create(seller=self.admin, name="Shared bundle", price=20, stock=0, product_type="bundle", approval_status="approved")
        for flavor, qty in [("Vanilla",2),("Chocolate",1)]:
            BundleComponent.objects.create(bundle=bundle, product=product, required_quantity=qty,
                selections=[{"group":"Size", "option":"Large"},{"group":"Flavor", "option":flavor}])
        response = self.order(1, product=bundle); self.assertEqual(response.status_code, 201, response.content)
        order = MarketplaceOrder.objects.get(pk=response.json()["order"]["id"])
        large = product.inventory_skus.get(variant_name="Large")
        self.assertEqual(large.batches.get().remaining_quantity, 2)
        self.assertEqual(sum(order.fifo_allocations.filter(batch__sku=large).values_list("quantity", flat=True)), 3)
        product.refresh_from_db(); product.customization_options[0]["options"][0]["name"] = "Renamed"
        with self.assertRaises(fifo.FIFOError): product.save()
        self.assertEqual(self.cancel(order).status_code, 200)
        self.assertEqual(large.batches.get().remaining_quantity, 5)

    def test_changed_dry_run_fingerprint_blocks_cutover_without_stock_changes(self):
        InventoryFIFOControl.objects.update(active=False)
        self.product.stock = 10; self.product.save()
        plan = fifo.reconciliation()
        self.product.stock = 11; self.product.save()
        with self.assertRaises(fifo.FIFOError): fifo.initialize(plan["fingerprint"])
        self.assertFalse(InventoryFIFOControl.objects.get(pk=1).active)
        self.assertFalse(InventoryBatch.objects.exists())
        self.product.refresh_from_db(); self.assertEqual(self.product.stock, 11)

    def test_cutover_command_checks_backup_identity_and_applies_only_in_test_database(self):
        import hashlib
        from tempfile import TemporaryDirectory
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        from django.db import connection
        InventoryFIFOControl.objects.update(active=False)
        self.product.stock = 10; self.product.save()
        plan = fifo.reconciliation()
        config = connection.settings_dict
        self.assertTrue(config["NAME"].startswith("test_"))
        with TemporaryDirectory() as folder:
            backup = Path(folder) / "isolated-test.dump"
            backup.write_bytes(b"Isolated verification fixture only." * 10)
            identity = hashlib.sha256(json.dumps({"host":str(config.get("HOST") or "localhost"),"port":str(config.get("PORT") or 5432),"name":config["NAME"]},sort_keys=True).encode()).hexdigest()
            manifest = {"database":config["NAME"],"database_identity":identity,"sha256":hashlib.sha256(backup.read_bytes()).hexdigest(),"opening_fingerprint":plan["fingerprint"],"restore_verified":True}
            marker = backup.with_suffix(".dump.verified.json")
            marker.write_text(json.dumps({**manifest,"database_identity":"wrong"}),encoding="utf-8")
            with self.assertRaises(CommandError): call_command("initialize_fifo_inventory",apply=True,backup_file=str(backup),expected_fingerprint=plan["fingerprint"],stdout=StringIO())
            marker.write_text(json.dumps(manifest),encoding="utf-8")
            call_command("initialize_fifo_inventory",apply=True,backup_file=str(backup),expected_fingerprint=plan["fingerprint"],stdout=StringIO())
        self.assertEqual(self.sku.batches.get().remaining_quantity,10)
        self.product.refresh_from_db(); self.assertEqual(self.product.stock,10)
