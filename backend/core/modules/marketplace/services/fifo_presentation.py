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
    if movement.reference:
        return movement.reference
    if movement.kind == "receipt" and movement.received_at is not None:
        return f"Receipt #{movement.pk}"
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


def search_movements(rows, search):
    from api.models import InventoryStockMovement
    from django.db.models import Q
    candidates = [row for row in rows if row.get("sku_id") and not row.get("derived")]
    matching = [row["sku_id"] for row in candidates if any(search in str(row[field]).casefold()
        for field in ("product_name", "name", "group", "sku", "seller_name"))]
    query = Q(sku_id__in=matching) | Q(order__order_code__icontains=search) | Q(notes__icontains=search) | Q(actor__icontains=search) | Q(reference__icontains=search)
    query |= Q(received_batches__transaction_reference__icontains=search)
    if search.upper().startswith("BAT-") and search[4:].isdecimal():
        query |= Q(fifo_allocations__batch_id=int(search[4:])) | Q(received_batches__pk=int(search[4:]))
    return InventoryStockMovement.objects.filter(sku_id__in=[row["sku_id"] for row in candidates]).filter(query).order_by()


def workspace(request, products, rows, params, *, batch_search=None, movement_search=None):
    section = request.GET.get("inventory_section", "overview")
    if section not in {"overview", "movements", "fifo"}: section = "overview"
    can_move = any(request.user.has_perm("accounts." + code) for code in ("can_manage_products", "can_approve_products", "can_view_stock_movements"))
    if section == "movements" and not can_move: section = "overview"
    base = {k: v for k, v in params.items() if k not in {"inventory_section", "page"}}
    context = {"fifo_ready": enabled(), "inventory_section": section, "fifo_can_move": can_move,
        "inventory_tabs": [{"key": key, "label": label, "url": reverse("admin_products_page") + "?" + urlencode({**base, "inventory_section": key})}
            for key, label in (("overview", "Stock Overview"), ("movements", "Stock Movements"), ("fifo", "Stock Batches")) if key != "movements" or can_move]}
    from api.models import InventoryBatch, InventoryStockMovement
    from django.db.models import Q
    from django.utils import timezone
    from .fifo import ordered_batches
    context["fifo_receive_now"] = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
    context["fifo_has_batches"] = InventoryBatch.objects.filter(sku__product__in=products).exists()
    ids = [row["sku_id"] for row in rows if not row.get("derived") and row.get("sku_id")]
    batches = ordered_batches(InventoryBatch.objects.filter(sku_id__in=ids).select_related(
        "sku__product__seller", "sku__product__mobile_seller", "receipt_movement"
    ).prefetch_related("allocations__movement"))
    if batch_search is not None:
        batches = batches.filter(pk__in=batch_search.values("pk"))
    context["fifo_batches"] = Paginator(batches, 30).get_page(request.GET.get("fifo_page"))
    for batch in context["fifo_batches"]:
        reserved = sum(row.quantity for row in batch.allocations.all() if row.state == "reserved")
        batch.reserved_quantity = reserved
        batch.physical_remaining_quantity = batch.remaining_quantity + reserved
        batch.consumed_quantity = sum(row.quantity for row in batch.allocations.all() if row.state == "consumed")
        batch.owner_label = batch.sku.product.owner.get_full_name().strip() or batch.sku.product.owner.username
        batch.history_url = reverse("admin_products_page") + "?" + urlencode({**base, "inventory_section": "movements", "search": batch.sku.code, "batch": batch.pk})
        batch.product_url = reverse("admin_products_page") + "?" + urlencode({"product_id": batch.sku.product_id,
            **({"__at": base["__at"]} if base.get("__at") else {})})
        batch.status_label = "Partially reserved" if batch.remaining_quantity and reserved else "Available" if batch.remaining_quantity else "Fully reserved" if reserved else "Depleted"
    if can_move:
        movements = InventoryStockMovement.objects.filter(sku_id__in=ids)
        if movement_search is not None:
            movements = movements.filter(pk__in=movement_search.values("pk"))
        if params.get("batch"):
            selected = batches.filter(pk=params["batch"]).first() if params["batch"].isdecimal() else None
            if selected:
                movements = movements.filter(Q(received_batches=selected) | Q(fifo_allocations__batch=selected)
                    | Q(order_id__in=selected.allocations.exclude(order_id=None).values("order_id"), sku=selected.sku)).distinct()
            else:
                movements = movements.none()
        context["fifo_movements"] = Paginator(movements.select_related("sku__product", "order").prefetch_related(
            "fifo_allocations__batch", "order__fifo_allocations__batch", "received_batches").order_by("-created_at", "-pk"), 30).get_page(request.GET.get("fifo_page"))
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
            movement.batch_references = ", ".join(dict.fromkeys(
                [row.batch.code for row in movement.display_allocations] + [batch.code for batch in movement.received_batches.all()]))
            if not movement.batch_references and movement.kind == "receipt" and movement.received_at is not None:
                movement.batch_references = "—"
    eligible = {p.pk for p in products.filter(product_type="single", approval_status="approved", is_archived=False)}
    context["fifo_receivable"] = [row for row in rows if row["product_id"] in eligible and row.get("sku_id") and not row.get("derived")]
    context["fifo_receiving_unavailable"] = not context["fifo_ready"] and any(row["inventory_method"] == "fifo" for row in context["fifo_receivable"])
    context["fifo_receivable"] = [row for row in context["fifo_receivable"] if row.get("can_receive") and (row["inventory_method"] == "simple" or context["fifo_ready"])]
    context["fifo_page_query"] = urlencode({**base, "inventory_section": section})
    return context
