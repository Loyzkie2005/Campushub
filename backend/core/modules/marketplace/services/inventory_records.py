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
    saved = type(product).objects.using(using).values("stock", "customization_options", "product_type", "name").get(pk=product.pk)
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
    previous = stock_points(**before) if before is not None else {}
    movements = []
    from . import fifo
    fifo_active = fifo.enabled()
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
            order_id=getattr(product, "_inventory_order_id", None), actor=getattr(product, "_inventory_actor", ""))
        if fifo_active:
            movement.save(using=using)
            fifo.sync_change(identities[key], old or 0, amount, movement, product)
        movements.append(movement)
    if movements:
        if not fifo_active:
            InventoryStockMovement.objects.using(using).bulk_create(movements)
        product._inventory_movement_ids = getattr(product, "_inventory_movement_ids", []) + [row.pk for row in movements]
    # A later ordinary save must not inherit an earlier reservation context.
    for attr in ("_inventory_kind", "_inventory_order_id", "_inventory_actor", "_fifo_receipt"):
        product.__dict__.pop(attr, None)


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
    from api.models import InventorySKU, InventoryStockMovement, Product
    from . import fifo
    fifo.complete(order)
    allocations = (order.customization or {}).get("bundle_components") or []
    ids = {row["product_id"] for row in allocations} if allocations else {order.product_id}
    products = {product.pk: product for product in Product.objects.filter(pk__in=ids)}
    identities = {(row.product_id, row.group_name, row.variant_name): row for row in InventorySKU.objects.filter(product_id__in=ids)}
    existing = set(order.inventory_movements.filter(kind="sale").values_list("sku_id", flat=True))
    events = []
    for product in products.values():
        keys = {(group, name) for product_id, group, name in identities if product_id == product.pk}
        for key, quantity in order_allocations(order, product, inventory_keys=keys).items():
            sku = identities.get((product.pk, *key))
            if sku and sku.pk not in existing:
                events.append(InventoryStockMovement(sku=sku, order=order, kind="sale", balance="on_hand", quantity_change=-quantity, actor=actor))
    InventoryStockMovement.objects.bulk_create(events)
