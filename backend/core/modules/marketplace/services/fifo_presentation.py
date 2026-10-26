"""Scoped, paginated projections for the existing Inventory workspace."""
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.urls import reverse

from .fifo import enabled


def movement_allocations(movement):
    if movement.order_id and movement.kind in {"release", "sale"}:
        return [row for row in movement.order.fifo_allocations.all() if row.batch.sku_id == movement.sku_id]
    return list(movement.fifo_allocations.all())


def movement_reference(movement):
    if movement.order_id:
        return "Order #" + (movement.order.order_code or str(movement.order_id))
    return next((batch.transaction_reference for batch in movement.received_batches.all()), "Stock record")


def search_batches(rows, search):
    """Search only authorized candidate SKUs and their existing human batch codes."""
    from api.models import InventoryBatch
    from django.db.models import CharField, Q, Value
    from django.db.models.functions import Cast, Concat, Greatest, Length, LPad
    candidates = [row for row in rows if row.get("sku_id") and not row.get("derived")]
    matching = [row["sku_id"] for row in candidates if any(search in str(row[field]).casefold()
        for field in ("product_name", "name", "group", "sku", "seller_name"))]
    digits = Cast("pk", output_field=CharField())
    reference = Concat(Value("BAT-"), LPad(digits, Greatest(Value(8), Length(digits)), Value("0")))
    return InventoryBatch.objects.filter(sku_id__in=[row["sku_id"] for row in candidates]).annotate(
        search_reference=reference).filter(Q(sku_id__in=matching) | Q(search_reference__icontains=search)).order_by()


def workspace(request, products, rows, params, *, batch_search=None):
    section = request.GET.get("inventory_section", "overview")
    if section not in {"overview", "movements", "fifo"}: section = "overview"
    can_move = any(request.user.has_perm("accounts." + code) for code in ("can_manage_products", "can_approve_products", "can_view_stock_movements"))
    if section == "movements" and not can_move: section = "overview"
    base = {k: v for k, v in params.items() if k not in {"inventory_section", "page"}}
    context = {"fifo_ready": enabled(), "inventory_section": section, "fifo_can_move": can_move,
        "inventory_tabs": [{"key": key, "label": label, "url": reverse("admin_products_page") + "?" + urlencode({**base, "inventory_section": key})}
            for key, label in (("overview", "Stock Overview"), ("movements", "Stock Movements"), ("fifo", "Stock Batches")) if key != "movements" or can_move]}
    if not context["fifo_ready"]: return context
    from api.models import InventoryBatch, InventoryStockMovement
    from django.db.models import Case, When, Value, IntegerField
    ids = [row["sku_id"] for row in rows if not row.get("derived") and row.get("sku_id")]
    batches = InventoryBatch.objects.filter(sku_id__in=ids).select_related(
        "sku__product__seller", "sku__product__mobile_seller", "receipt_movement"
    ).prefetch_related("allocations__movement").annotate(
        opening_first=Case(When(origin="opening", then=Value(0)), default=Value(1), output_field=IntegerField())).order_by("opening_first", "recorded_at", "pk")
    if batch_search is not None:
        batches = batches.filter(pk__in=batch_search.values("pk"))
    context["fifo_batches"] = Paginator(batches, 30).get_page(request.GET.get("fifo_page"))
    for batch in context["fifo_batches"]:
        reserved = sum(row.quantity for row in batch.allocations.all() if row.state == "reserved")
        batch.reserved_quantity = reserved
        batch.consumed_quantity = sum(row.quantity for row in batch.allocations.all() if row.state == "consumed")
        batch.owner_label = batch.sku.product.owner.get_full_name().strip() or batch.sku.product.owner.username
        batch.status_label = "Partially reserved" if batch.remaining_quantity and reserved else "Available" if batch.remaining_quantity else "Fully reserved" if reserved else "Depleted"
    if can_move:
        context["fifo_movements"] = Paginator(InventoryStockMovement.objects.filter(sku_id__in=ids).select_related("sku__product", "order").prefetch_related("fifo_allocations__batch", "order__fifo_allocations__batch", "received_batches").order_by("-created_at", "-pk"), 30).get_page(request.GET.get("fifo_page"))
        for movement in context["fifo_movements"]:
            movement.display_allocations = movement_allocations(movement)
            movement.allocation_reconciled = False
            if movement.kind == "reservation" and movement.order_id and not movement.display_allocations:
                # Existing opening holds have an order/SKU link, not a historical
                # movement link. Present that provenance without backfilling it.
                movement.display_allocations = [row for row in movement.order.fifo_allocations.all()
                    if row.legacy and row.movement_id is None and row.batch.sku_id == movement.sku_id]
                movement.allocation_reconciled = bool(movement.display_allocations)
            movement.transaction_label = movement_reference(movement)
    eligible = {p.pk for p in products.filter(product_type="single", approval_status="approved", is_archived=False)}
    context["fifo_receivable"] = [row for row in rows if row["product_id"] in eligible and row.get("sku_id") and not row.get("derived")]
    context["fifo_page_query"] = urlencode({**base, "inventory_section": section})
    return context
