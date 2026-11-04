"""Persist SKU identities and observed movements without duplicating stock."""
from django.utils.text import slugify


def sku_parts(product, variant="", *, name=None, product_type=None):
    kind = product.product_type if product_type is None else product_type
    name = product.name if name is None else name
    prefix = "BND" if kind == product.TYPE_BUNDLE else (slugify(name).replace("-", "")[:3].upper() or "ITM")
    short = "".join(word[0] for word in slugify(variant).split("-") if word)[:4].upper()
    return prefix, short


def stock_points(stock, customization_options, product_type):
    """Return actual stock pools, excluding untracked choices and bundle sums."""
    from .inventory import flatten_customization_inventory
    if product_type == "bundle":
        return {}
    variants = flatten_customization_inventory(customization_options)
    if variants:
        return {(row["group_name"], row["variant_name"]): row["stock"] for row in variants}
    return {("", ""): max(int(stock or 0), 0)}


def sync_inventory_records(product, *, before=None, using="default"):
    """Called inside Product.save's transaction; no changes to quantity formulas."""
    from api.models import InventorySKU, InventoryStockMovement
    # Partial saves and F expressions must use what was actually persisted.
    saved = type(product).objects.using(using).values("stock", "customization_options", "product_type", "name", "inventory_method").get(pk=product.pk)
    current = stock_points(saved["stock"], saved["customization_options"], saved["product_type"])
    keys = {("", ""), *current.keys()}
    identities = {(row.group_name, row.variant_name): row for row in InventorySKU.objects.using(using).filter(product_id=product.pk)}
    missing = []
    for group, name in sorted(keys - identities.keys()):
        prefix, short = sku_parts(product, name, name=saved["name"], product_type=saved["product_type"])
        missing.append(InventorySKU(product=product, group_name=group, variant_name=name, prefix=prefix, variant_code=short))
    if missing:
        InventorySKU.objects.using(using).bulk_create(missing, ignore_conflicts=True)
        identities = {(row.group_name, row.variant_name): row for row in InventorySKU.objects.using(using).filter(product_id=product.pk)}
    previous = stock_points(**{key: before[key] for key in ("stock", "customization_options", "product_type")}) if before is not None else {}
    movements = []
    from . import fifo
    method = saved["inventory_method"]
    if method not in {"simple", "fifo"} or (saved["product_type"] == "bundle" and method != "simple"):
        raise fifo.FIFOError("Choose Simple stock or FIFO batches for a single product. Bundles use their components' stock.")
    fifo_active = method == "fifo" and fifo.enabled()
    if method == "fifo" and not fifo_active:
        raise fifo.FIFOError("Stock receiving is not configured. Contact your system administrator.")
    if before and before["inventory_method"] != method:
        if fifo_active:
            from copy import copy
            source = copy(product)
            for field in ("stock", "customization_options", "product_type"):
                setattr(source, field, before[field])
            fifo.initialize_product(source, previous, identities)
        else:
            fifo.check_simple_transition(product)
    receipt = getattr(product, "_fifo_receipt", None)
    simple_balances = None
    # Retired variant pools must also be reconciled when FIFO is active.
    points = {**({key: 0 for key in previous} if fifo_active else {}), **current}
    if fifo_active:
        from api.models import InventoryBatchAllocation
        for key in previous.keys() - current.keys():
            if InventoryBatchAllocation.objects.filter(batch__sku=identities[key], state="reserved").exists():
                raise fifo.FIFOError("Reserved FIFO variants cannot be removed or converted before their orders are resolved.")
    for key, amount in points.items():
        old = previous.get(key)
        if old == amount:
            continue
        movement = InventoryStockMovement(sku=identities[key],
            kind="opening" if old is None else getattr(product, "_inventory_kind", "adjustment"),
            quantity_change=amount if old is None else amount - old,
            available_before=0 if old is None else old, available_after=amount,
            order_id=getattr(product, "_inventory_order_id", None), actor=getattr(product, "_inventory_actor", ""),
            notes=getattr(product, "_inventory_notes", None),
            reference=receipt["reference"] if receipt else None,
            received_at=receipt["received_at"] if receipt else None)
        if fifo_active:
            if movement.kind in {"opening", "receipt", "adjustment"}:
                from django.db.models import Sum
                reserved = InventoryBatchAllocation.objects.filter(batch__sku=identities[key], state="reserved").aggregate(total=Sum("quantity"))["total"] or 0
                movement.balance = "on_hand"
                movement.available_before = (old or 0) + reserved
                movement.available_after = amount + reserved
            movement.save(using=using)
            fifo.sync_change(identities[key], old or 0, amount, movement, product)
        elif movement.kind in {"opening", "receipt", "adjustment"}:
            if simple_balances is None:
                simple_balances = physical_points(type(product).objects.using(using).get(pk=product.pk))
            physical = simple_balances.get(key)
            if physical is not None:
                movement.balance = "on_hand"
                movement.available_before = physical - movement.quantity_change
                movement.available_after = physical
        movements.append(movement)
    if movements:
        if not fifo_active:
            InventoryStockMovement.objects.using(using).bulk_create(movements)
        product._inventory_movement_ids = getattr(product, "_inventory_movement_ids", []) + [row.pk for row in movements]
    # A later ordinary save must not inherit an earlier reservation context.
    for attr in ("_inventory_kind", "_inventory_order_id", "_inventory_actor", "_inventory_notes", "_fifo_receipt"):
        product.__dict__.pop(attr, None)


def physical_points(product):
    """Canonical available + live holds, including simple products without batches."""
    from .inventory import get_product_inventory_snapshot
    snapshot = get_product_inventory_snapshot(product)
    if snapshot is None:
        return {}
    return {(row["group"], row["name"]): row["on_hand"] for row in snapshot["variant_thresholds"]} or {("", ""): snapshot["on_hand"]}


def attach_reservation_movements(product, order):
    from api.models import InventoryStockMovement
    ids = product.__dict__.pop("_inventory_movement_ids", [])
    if ids:
        InventoryStockMovement.objects.filter(pk__in=ids, kind="reservation", order__isnull=True).update(order=order)
        from . import fifo
        fifo.attach(order, ids)


def order_allocations(order, product, *, inventory_keys=None):
    """Purchased component snapshots take precedence over today's bundle recipe."""
    from .customization import parse_order_selections
    from .inventory import _selected_stock_options, product_variant_items
    if inventory_keys is None:
        inventory_keys = {(sku.group_name, sku.variant_name) for sku in product.inventory_skus.all()}
    tracked_keys = set(inventory_keys) - {("", "")}
    allocations = (order.customization or {}).get("bundle_components")
    if allocations:
        sources = [(row.get("selections") or [], order.quantity * row["required_quantity"])
                   for row in allocations if row.get("product_id") == product.pk]
    elif order.product_id == product.pk:
        sources = [(parse_order_selections(order.customization), order.quantity)]
    else:
        sources = []
    result = {}
    for selections, quantity in sources:
        selected_keys = {(row["group"], row["option"]) for row in selections}
        if selected_keys & tracked_keys:
            # Retired identities remain valid even after conversion to simple stock.
            keys = selected_keys & tracked_keys
        elif product_variant_items(product):
            # Use names stored on the order, including a retired variant's name.
            keys = selected_keys
            if not keys:
                chosen = _selected_stock_options(product.customization_options, [])
                keys = {(group.get("name") or "", option.get("name") or "")
                        for group in product.customization_options for option in group.get("options") or []
                        if any(option is item for item in chosen)}
        else:
            keys = {("", "")}
        for key in keys:
            result[key] = result.get(key, 0) + quantity
    return result


def record_completed_sale(order, actor=""):
    """Completion changes physical On Hand, without deducting Available again."""
    from api.models import InventorySKU, InventoryStockMovement, InventoryBatch, InventoryBatchAllocation, Product
    from . import fifo
    allocations = (order.customization or {}).get("bundle_components") or []
    ids = {row["product_id"] for row in allocations} if allocations else {order.product_id}
    products = {product.pk: product for product in Product.objects.select_for_update().filter(pk__in=ids).order_by("pk")}
    identities = {(row.product_id, row.group_name, row.variant_name): row for row in InventorySKU.objects.filter(product_id__in=ids)}
    existing = set(order.inventory_movements.filter(kind="sale").values_list("sku_id", flat=True))
    balances = {}
    if fifo.enabled():
        from django.db.models import Sum
        for sku in identities.values():
            if products[sku.product_id].inventory_method != "fifo":
                continue
            available = InventoryBatch.objects.filter(sku=sku).aggregate(total=Sum("remaining_quantity"))["total"] or 0
            reserved = InventoryBatchAllocation.objects.filter(batch__sku=sku, state="reserved").aggregate(total=Sum("quantity"))["total"] or 0
            balances[sku.pk] = available + reserved
    fifo.complete(order)
    events = []
    for product in products.values():
        simple_after = physical_points(product) if product.inventory_method == "simple" else {}
        keys = {(group, name) for product_id, group, name in identities if product_id == product.pk}
        for key, quantity in order_allocations(order, product, inventory_keys=keys).items():
            sku = identities.get((product.pk, *key))
            if sku and sku.pk not in existing:
                before = balances.get(sku.pk)
                if key in simple_after:
                    before = simple_after[key] + quantity
                events.append(InventoryStockMovement(sku=sku, order=order, kind="sale", balance="on_hand", quantity_change=-quantity,
                    available_before=before, available_after=before - quantity if before is not None else None, actor=actor))
    InventoryStockMovement.objects.bulk_create(events)
