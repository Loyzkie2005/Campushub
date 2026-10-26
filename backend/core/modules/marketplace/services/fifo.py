"""FIFO ledger behind existing available stock; activation requires explicit cutover."""
import hashlib
import json
from functools import wraps
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import Case, IntegerField, Sum, Value, When
from django.http import JsonResponse
from django.utils import timezone

from .inventory import InsufficientStockError


class FIFOError(InsufficientStockError):
    pass


def enabled():
    if not getattr(settings, "CAMPUSHUB_FIFO_ENABLED", False):
        return False  # Safe before the working database has the additive tables.
    from api.models import InventoryFIFOControl
    return InventoryFIFOControl.objects.filter(pk=1, active=True).exists()


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def operation(kind, key, payload):
    from api.models import InventoryOperation
    try:
        key = UUID(str(key))
    except (ValueError, TypeError, AttributeError) as exc:
        raise FIFOError("Use a valid submission key. Reload the form and retry.") from exc
    digest = fingerprint(payload)
    record, _ = InventoryOperation.objects.get_or_create(kind=kind, key=key, defaults={"fingerprint": digest})
    record = InventoryOperation.objects.select_for_update().get(pk=record.pk)
    if record.fingerprint != digest:
        raise FIFOError("This submission key was already used with different details.")
    return record


def sync_change(sku, old, new, movement, product):
    """Called under Product.save's lock/transaction for every real stock delta."""
    from api.models import InventoryBatch, InventoryBatchAllocation
    batches = list(InventoryBatch.objects.select_for_update().filter(sku=sku).annotate(
        opening_first=Case(When(origin="opening", then=Value(0)), default=Value(1), output_field=IntegerField())
    ).order_by("opening_first", "recorded_at", "pk"))
    if sum(batch.remaining_quantity for batch in batches) != old:
        raise FIFOError("Batch balance does not match available stock. Reconcile inventory before continuing.")
    delta = new - old
    if delta > 0 and movement.kind == "release":
        allocations = list(InventoryBatchAllocation.objects.select_for_update().filter(
            order_id=movement.order_id, batch__sku=sku, state="reserved").order_by("batch_id", "pk"))
        if not movement.order_id or sum(row.quantity for row in allocations) != delta:
            raise FIFOError("Original batch allocations cannot be reconciled. Cancellation was blocked.")
        batch_map = {batch.pk: batch for batch in batches}
        for row in allocations:
            batch = batch_map[row.batch_id]
            batch.remaining_quantity += row.quantity
            batch.save(update_fields=["remaining_quantity"])
            row.state = "released"; row.resolved_at = timezone.now()
            row.save(update_fields=["state", "resolved_at"])
    elif delta > 0:
        receipt = getattr(product, "_fifo_receipt", None)
        InventoryBatch.objects.create(sku=sku, receipt_movement=movement, origin="receipt" if receipt else "adjustment",
            initial_quantity=delta, remaining_quantity=delta, received_at=timezone.now() if receipt else None,
            transaction_reference=receipt["reference"] if receipt else "Stock adjustment",
            received_by_id=receipt["user_id"] if receipt else None, actor=movement.actor)
    elif delta < 0:
        if movement.kind == "reservation":
            from .inventory import get_inventory_status, parse_expiry_date
            expiry = product.expiry_date
            if sku.variant_name:
                expiry = next((parse_expiry_date(option.get("expiry_date")) for group in product.customization_options
                    for option in group["options"] if (group["name"], option["name"]) == (sku.group_name, sku.variant_name)), None)
            if get_inventory_status(stock=old, category=product.category, expiry_date=expiry) == "expired":
                raise FIFOError("Expired inventory cannot be reserved.")
        remaining = -delta
        for batch in batches:
            take = min(batch.remaining_quantity, remaining)
            if take:
                batch.remaining_quantity -= take; batch.save(update_fields=["remaining_quantity"])
                InventoryBatchAllocation.objects.create(batch=batch, movement=movement, quantity=take,
                    order_id=movement.order_id, state="reserved" if movement.kind == "reservation" else "adjustment")
                remaining -= take
            if not remaining:
                break
        if remaining:
            raise FIFOError("Stock batches have insufficient available stock.")


def attach(order, movement_ids):
    if enabled():
        from api.models import InventoryBatchAllocation
        InventoryBatchAllocation.objects.filter(movement_id__in=movement_ids, state="reserved", order__isnull=True).update(
            order=order, order_reference=order.order_code or str(order.pk))


def complete(order):
    if enabled():
        from api.models import InventoryBatchAllocation
        InventoryBatchAllocation.objects.filter(order=order, state="reserved").update(state="consumed", resolved_at=timezone.now())


@transaction.atomic
def receive(sku_id, quantity, reference, user, key):
    from api.models import InventorySKU, Product
    from .product_access import admin_product_queryset
    from .inventory import validate_stock_quantity
    if not user.has_perm("accounts.can_manage_products"):
        raise FIFOError("Receiving requires Manage Products permission.")
    if not enabled():
        raise FIFOError("Stock receiving is not available yet. Contact your system administrator.")
    try:
        quantity = validate_stock_quantity(quantity)
    except ValueError as exc:
        raise FIFOError("Enter a positive whole receiving quantity.") from exc
    reference = str(reference or "").strip()
    if quantity < 1 or quantity > 2147483647 or not reference or len(reference) > 150:
        raise FIFOError("Enter a positive quantity and a transaction reference of at most 150 characters.")
    record = operation("receipt", key, {"sku": str(sku_id), "quantity": quantity, "reference": reference, "user": user.pk})
    if record.response is not None:
        return record.response
    identity = InventorySKU.objects.filter(pk=sku_id, product__in=admin_product_queryset(user)).first()
    if identity is None:
        raise FIFOError("Inventory item is outside your authorized scope.")
    product = Product.objects.select_for_update().get(pk=identity.product_id)
    if product.product_type == "bundle" or product.is_archived or product.approval_status != Product.STATUS_APPROVED or not product.owner.is_active:
        raise FIFOError("Receive stock only for active approved single products or their exact variants.")
    from .inventory_records import stock_points
    points = stock_points(product.stock, product.customization_options, product.product_type)
    point = (identity.group_name, identity.variant_name)
    if point not in points or points[point] + quantity > 2147483647:
        raise FIFOError("Select a current inventory SKU within the supported quantity limit.")
    if point == ("", ""):
        product.stock += quantity
    else:
        for group in product.customization_options:
            for option in group["options"]:
                if (group["name"], option["name"]) == point:
                    option["stock"] += quantity
        from .inventory import sync_product_inventory_fields
        sync_product_inventory_fields(product)
    product._inventory_kind = "receipt"
    if product.stock > 2147483647:
        raise FIFOError("Total product stock exceeds the supported quantity limit.")
    product._inventory_actor = user.get_full_name().strip() or user.username
    product._fifo_receipt = {"reference": reference, "user_id": user.pk}
    product.save(update_fields=["stock", "customization_options", "updated_at"])
    batch = identity.batches.order_by("-pk").first()
    record.response = {"message": "Stock received.", "batch": batch.code, "quantity": quantity}
    record.save(update_fields=["response"])
    return record.response


def order_request(view):
    """Optional keyed order retries; unkeyed clients retain their existing contract."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        key = request.headers.get("Idempotency-Key")
        if request.method != "POST" or not key or not enabled():
            return view(request, *args, **kwargs)
        class Rejected(Exception):
            def __init__(self, response): self.response = response
        try:
            payload = json.loads(request.body)
            with transaction.atomic():
                record = operation("order", key, payload)
                if record.response is not None:
                    return JsonResponse(record.response, status=record.status_code)
                response = view(request, *args, **kwargs)
                if response.status_code >= 400:
                    raise Rejected(response)
                record.response = json.loads(response.content); record.status_code = response.status_code
                record.save(update_fields=["response", "status_code"])
                return response
        except Rejected as exc:
            return exc.response
        except (ValueError, FIFOError) as exc:
            return JsonResponse({"error": str(exc)}, status=409)
    return wrapped


def reconciliation():
    """Read-only plan; historical receipt dates are deliberately absent."""
    from api.models import Product, MarketplaceOrder
    from .inventory_records import stock_points, order_allocations
    products = list(Product.objects.prefetch_related("inventory_skus").order_by("pk"))
    holds = list(MarketplaceOrder.objects.filter(inventory_deducted=True, inventory_restored=False,
        status__in=("pending", "processing", "ready_for_pickup")).order_by("pk"))
    rows, errors = [], []
    for product in products:
        points = stock_points(product.stock, product.customization_options, product.product_type)
        for point, available in points.items():
            sku = next((s for s in product.inventory_skus.all() if (s.group_name, s.variant_name) == point), None)
            allocations = [{"order": order.pk, "reference": order.order_code, "quantity": quantity}
                for order in holds if (quantity := order_allocations(order, product).get(point, 0))]
            if sku is None:
                errors.append(f"Product {product.pk}: missing SKU {point}."); continue
            reserved = sum(row["quantity"] for row in allocations)
            if available + reserved > 2147483647:
                errors.append(f"SKU {sku.pk}: opening balance exceeds the supported quantity limit.")
            rows.append({"sku": sku.pk, "product": product.pk, "group": point[0], "variant": point[1],
                "available": available, "reserved": reserved, "opening_quantity": available + reserved, "holds": allocations})
        if product.product_type != "bundle":
            for order in holds:
                if any(key not in points for key in order_allocations(order, product)):
                    errors.append(f"Order {order.pk}: retired or missing variant on product {product.pk}.")
    known_ids = {p.pk for p in products}
    for order in holds:
        ids = {row["product_id"] for row in (order.customization or {}).get("bundle_components", [])} or {order.product_id}
        if not ids.issubset(known_ids): errors.append(f"Order {order.pk}: missing original product.")
    result = {"rows": rows, "errors": errors}
    result["fingerprint"] = fingerprint(result)
    return result


@transaction.atomic
def initialize(expected):
    """Explicit cutover only; caller must verify backup and freeze stock writers."""
    from api.models import Product, MarketplaceOrder, InventoryFIFOControl, InventoryBatch, InventoryBatchAllocation
    if not getattr(settings, "CAMPUSHUB_FIFO_ENABLED", False):
        raise FIFOError("Enable the FIFO configuration during the approved write freeze before cutover.")
    list(MarketplaceOrder.objects.select_for_update().order_by("pk"))
    list(Product.objects.select_for_update().order_by("pk"))
    control, _ = InventoryFIFOControl.objects.get_or_create(pk=1)
    control = InventoryFIFOControl.objects.select_for_update().get(pk=1)
    if control.active or InventoryBatch.objects.exists():
        raise FIFOError("FIFO is already initialized or has batches. Cutover cannot be repeated.")
    plan = reconciliation()
    if plan["errors"] or plan["fingerprint"] != expected:
        raise FIFOError("Reconciliation changed or contains mismatches. Cutover blocked; run dry-run again.")
    for row in plan["rows"]:
        if not row["opening_quantity"]: continue
        batch = InventoryBatch.objects.create(sku_id=row["sku"], origin="opening", initial_quantity=row["opening_quantity"],
            remaining_quantity=row["available"], transaction_reference="FIFO cutover opening balance")
        for hold in row["holds"]:
            InventoryBatchAllocation.objects.create(batch=batch, order_id=hold["order"], order_reference=hold["reference"] or "",
                quantity=hold["quantity"], state="reserved", legacy=True)
    control.active = True; control.initialized_at = timezone.now()
    control.save(update_fields=["active", "initialized_at"])
    return plan
