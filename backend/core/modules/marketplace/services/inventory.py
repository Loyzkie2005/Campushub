from datetime import date, timedelta

from django.conf import settings
from django.utils import timezone

PERISHABLE_CATEGORIES = frozenset({
    "Rice Meals",
    "Snacks",
    "Desserts",
    "Beverages",
    "Combo Meals",
    "Breakfast",
})

INVENTORY_STATUS_IN_STOCK = "in_stock"
INVENTORY_STATUS_LOW_STOCK = "low_stock"
INVENTORY_STATUS_OUT_OF_STOCK = "out_of_stock"
INVENTORY_STATUS_PARTIALLY_AVAILABLE = "partially_available"
INVENTORY_STATUS_EXPIRING_SOON = "expiring_soon"
INVENTORY_STATUS_EXPIRED = "expired"

INVENTORY_STATUS_LABELS = {
    INVENTORY_STATUS_IN_STOCK: "In Stock",
    INVENTORY_STATUS_LOW_STOCK: "Low Stock",
    INVENTORY_STATUS_OUT_OF_STOCK: "Out of Stock",
    INVENTORY_STATUS_PARTIALLY_AVAILABLE: "Partially Available",
    INVENTORY_STATUS_EXPIRING_SOON: "Expiring Soon",
    INVENTORY_STATUS_EXPIRED: "Expired",
}

INVENTORY_STATUS_PRIORITY = (
    INVENTORY_STATUS_EXPIRED,
    INVENTORY_STATUS_OUT_OF_STOCK,
    INVENTORY_STATUS_EXPIRING_SOON,
    INVENTORY_STATUS_LOW_STOCK,
    INVENTORY_STATUS_PARTIALLY_AVAILABLE,
    INVENTORY_STATUS_IN_STOCK,
)


def low_stock_threshold(product=None, *, option=None):
    value = (option.get("low_stock_threshold") if option is not None
             else getattr(product, "low_stock_threshold", None))
    return int(value if value is not None else getattr(settings, "CAMPUSHUB_LOW_STOCK_THRESHOLD", 5))


class InventoryThresholdError(ValueError):
    """An explicit stock-warning level is invalid."""


class InventoryStockError(ValueError):
    """Stock input or a requested variant change cannot be applied safely."""


def validate_stock_quantity(value):
    raw = str(value).strip()
    if isinstance(value, bool) or not raw.isdecimal():
        raise InventoryStockError("Stock Quantity must be a whole number of 0 or greater.")
    return int(raw)


def validate_low_stock_threshold(value, *, stock=None, initial=False):
    raw = str(value).strip()
    if isinstance(value, bool) or not raw.isdecimal():
        raise InventoryThresholdError("Low Stock Threshold must be a whole number of 0 or greater.")
    threshold = int(raw)
    if initial and stock is not None and threshold >= stock and not (stock == threshold == 0):
        raise InventoryThresholdError("Low Stock Threshold must be lower than the initial stock quantity.")
    return threshold


def expiry_warning_days():
    return int(getattr(settings, "CAMPUSHUB_EXPIRY_WARNING_DAYS", 7))


def is_perishable_category(category):
    return (category or "").strip() in PERISHABLE_CATEGORIES


def get_inventory_status(*, stock, expiry_date=None, category=None, today=None, threshold=None):
    today = today or timezone.localdate()
    threshold = low_stock_threshold() if threshold is None else threshold
    warning_days = expiry_warning_days()
    perishable = is_perishable_category(category)

    if perishable and expiry_date and expiry_date < today:
        return INVENTORY_STATUS_EXPIRED
    if stock <= 0:
        return INVENTORY_STATUS_OUT_OF_STOCK
    if stock <= threshold:
        return INVENTORY_STATUS_LOW_STOCK
    if perishable and expiry_date and expiry_date <= today + timedelta(days=warning_days):
        return INVENTORY_STATUS_EXPIRING_SOON
    return INVENTORY_STATUS_IN_STOCK


def get_inventory_status_label(status):
    return INVENTORY_STATUS_LABELS.get(status, "In Stock")


def _worst_inventory_status(statuses):
    for status in INVENTORY_STATUS_PRIORITY:
        if status in statuses:
            return status
    return INVENTORY_STATUS_IN_STOCK


def flatten_customization_inventory(customization_options):
    items = []
    for group_index, group in enumerate(customization_options or []):
        if not isinstance(group, dict):
            continue
        for option_index, opt in enumerate(group.get("options") or []):
            if not isinstance(opt, dict) or "stock" not in opt:
                continue
            stock_raw = opt.get("stock", 0)
            try:
                stock = max(int(stock_raw), 0)
            except (TypeError, ValueError):
                stock = 0
            expiry_raw = (opt.get("expiry_date") or "").strip()
            expiry_date = None
            if expiry_raw:
                try:
                    expiry_date = parse_expiry_date(expiry_raw)
                except ValueError:
                    expiry_date = None
            items.append({"stock": stock, "expiry_date": expiry_date,
                          "low_stock_threshold": low_stock_threshold(option=opt),
                          "group_name": str(group.get("name") or ""),
                          "variant_name": str(opt.get("name") or ""),
                          "image_url": opt.get("image") or "",
                          "variant_key": f"{group_index}:{option_index}"})
    return items


def iter_product_low_stock(product, today=None, *, include_out_of_stock=False):
    """Positive available stock only, using the same expiry/option rules as Inventory.

    Stock is already deducted when orders reserve it. Never subtract orders again.
    Options have JSON positions, not separate ProductVariant database IDs.
    The dashboard may opt into depleted-stock alerts; the default stays low-only.
    """
    from .bundles import is_bundle
    if is_bundle(product):
        return  # Warning levels belong to the components, never a derived bundle.
    items = product_variant_items(product)
    if not items:
        items = [{"stock": get_product_total_stock(product), "expiry_date": product.expiry_date,
                  "low_stock_threshold": low_stock_threshold(product),
                  "group_name": "", "variant_name": "", "variant_key": ""}]
    for item in items:
        threshold = item["low_stock_threshold"]
        status = get_inventory_status(stock=item["stock"], expiry_date=item["expiry_date"],
                                category=product.category, today=today,
                                threshold=threshold)
        if status == INVENTORY_STATUS_LOW_STOCK or (include_out_of_stock and status == INVENTORY_STATUS_OUT_OF_STOCK):
            yield {"product": product, "available": item["stock"], "threshold": threshold,
                   "status": status,
                   "variant_name": item["variant_name"], "group_name": item["group_name"],
                   "image_url": item.get("image_url") or "",
                   "variant_key": item["variant_key"]}


def low_stock_inventory_rows(products, *, limit=5, today=None, include_out_of_stock=False):
    """Bounded-memory shortlist; two queries, with no seller/option N+1 lookups."""
    from heapq import nsmallest
    from itertools import chain
    from django.db.models import Case, When, F, FloatField, Q, Value
    from django.db.models.functions import Cast, Coalesce, NullIf, Trim

    today = today or timezone.localdate()
    if limit < 1:
        return []
    fields = ("id", "name", "stock", "category", "expiry_date", "image_url",
              "customization_enabled", "customization_options", "low_stock_threshold", "product_type")
    active = products.filter(is_archived=False, product_type="single")
    simple = active.annotate(effective_threshold=Coalesce("low_stock_threshold", Value(low_stock_threshold())))
    simple = simple.filter(customization_options=[], stock__lte=F("effective_threshold"),
                           **{"stock__gte" if include_out_of_stock else "stock__gt": 0})
    simple = simple.annotate(inventory_category=Trim("category")).exclude(
        Q(inventory_category__in=PERISHABLE_CATEGORIES, expiry_date__lt=today)
    ).annotate(criticality=Cast("stock", FloatField()) / NullIf(
        Cast("effective_threshold", FloatField()), Value(0.0)
    )).annotate(depleted_priority=Case(When(stock=0, then=Value(0)), default=Value(1)))
    simple = simple.only(*fields).order_by("depleted_priority", "criticality", "stock", "pk")[:limit]
    # JSON options cannot be sliced by product before ranking individual variants.
    # Stream only required fields and retain at most `limit` results in memory.
    options = active.exclude(customization_options=[]).only(*fields).order_by("pk").iterator(chunk_size=500)
    entries = (entry for product in chain(simple, options)
               for entry in iter_product_low_stock(product, today=today, include_out_of_stock=include_out_of_stock))
    return nsmallest(limit, entries, key=lambda row: (
        row["available"] / (row["threshold"] or 1), row["available"], row["product"].pk, row["variant_key"],
    ))


def get_availability_from_options(option_items, category, today=None):
    if not option_items:
        return INVENTORY_STATUS_IN_STOCK

    today = today or timezone.localdate()
    statuses = [
        get_inventory_status(
            stock=item["stock"],
            expiry_date=item["expiry_date"],
            category=category,
            today=today,
            threshold=item.get("low_stock_threshold"),
        )
        for item in option_items
    ]
    stocks = [item["stock"] for item in option_items]

    if all(stock <= 0 for stock in stocks):
        return INVENTORY_STATUS_OUT_OF_STOCK

    if any(stock <= 0 for stock in stocks) and any(stock > 0 for stock in stocks):
        worst = _worst_inventory_status([status for status, stock in zip(statuses, stocks) if stock > 0])
        if worst in {
            INVENTORY_STATUS_IN_STOCK,
            INVENTORY_STATUS_LOW_STOCK,
            INVENTORY_STATUS_EXPIRING_SOON,
        }:
            return INVENTORY_STATUS_PARTIALLY_AVAILABLE
        return worst

    return _worst_inventory_status(statuses)


def has_customization_options(customization_options):
    for group in customization_options or []:
        if not isinstance(group, dict):
            continue
        for opt in group.get("options") or []:
            if isinstance(opt, dict):
                return True
    return False


def count_customization_options(customization_options):
    total = 0
    for group in customization_options or []:
        if not isinstance(group, dict):
            continue
        total += sum(
            1 for opt in group.get("options") or [] if isinstance(opt, dict)
        )
    return total


def customization_has_stock_tracking(customization_options):
    for group in customization_options or []:
        if not isinstance(group, dict):
            continue
        for opt in group.get("options") or []:
            if isinstance(opt, dict) and "stock" in opt:
                return True
    return False


def product_variant_items(product):
    if not product.customization_options:
        return []
    if not customization_has_stock_tracking(product.customization_options):
        return []
    return flatten_customization_inventory(product.customization_options)


def uses_variant_inventory(product):
    return bool(product_variant_items(product))


def get_product_total_stock(product):
    from .bundles import is_bundle, bundle_inventory
    if is_bundle(product):
        return bundle_inventory(product)["available"]
    opts = product.customization_options or []
    if product.customization_enabled and has_customization_options(opts):
        if customization_has_stock_tracking(opts):
            items = flatten_customization_inventory(opts)
            return sum(item["stock"] for item in items)
        return max(int(product.stock or 0), 0)
    items = product_variant_items(product)
    if items:
        return sum(item["stock"] for item in items)
    return max(int(product.stock or 0), 0)


def get_product_inventory_status(product, today=None):
    from .bundles import is_bundle
    if is_bundle(product):
        return INVENTORY_STATUS_IN_STOCK if get_product_total_stock(product) > 0 else INVENTORY_STATUS_OUT_OF_STOCK
    today = today or timezone.localdate()
    opts = product.customization_options or []
    if product.customization_enabled and has_customization_options(opts):
        if customization_has_stock_tracking(opts):
            items = flatten_customization_inventory(opts)
            return get_availability_from_options(items, product.category, today=today)
        return get_inventory_status(
            stock=product.stock,
            expiry_date=product.expiry_date if is_perishable_category(product.category) else None,
            category=product.category,
            today=today,
            threshold=low_stock_threshold(product),
        )
    items = product_variant_items(product)
    if items:
        return get_availability_from_options(items, product.category, today=today)
    return get_inventory_status(
        stock=product.stock,
        expiry_date=product.expiry_date if is_perishable_category(product.category) else None,
        category=product.category,
        today=today,
        threshold=low_stock_threshold(product),
    )


def get_product_quantity_status(product):
    """Three parent display states; each separately tracked option keeps its level."""
    available = get_product_total_stock(product)
    if available <= 0:
        return INVENTORY_STATUS_OUT_OF_STOCK
    from .bundles import is_bundle
    if is_bundle(product):
        return INVENTORY_STATUS_IN_STOCK
    items = product_variant_items(product)
    if items:
        return (INVENTORY_STATUS_LOW_STOCK if any(
            0 < item["stock"] <= item["low_stock_threshold"] for item in items
        ) else INVENTORY_STATUS_IN_STOCK)
    return get_inventory_status(stock=available, threshold=low_stock_threshold(product))


def get_variant_stock_summary(product):
    items = product_variant_items(product)
    return {"variant_count": len(items),
            "low_stock_variant_count": sum(0 < item["stock"] <= item["low_stock_threshold"] for item in items),
            "out_of_stock_variant_count": sum(item["stock"] <= 0 for item in items)}


def sync_product_inventory_fields(product):
    """Align product-level stock/expiry with variation options when present."""
    items = product_variant_items(product)
    if items:
        product.stock = sum(item["stock"] for item in items)
        expiry_dates = [
            item["expiry_date"]
            for item in items
            if item["expiry_date"] is not None
        ]
        product.expiry_date = min(expiry_dates) if expiry_dates else None
        return
    product.stock = max(int(product.stock or 0), 0)


class InsufficientStockError(ValueError):
    """Raised when an order requests inventory that is not available."""


def _selected_option_keys(selections):
    return {
        ((row.get("group") or "").strip(), (row.get("option") or "").strip())
        for row in selections or []
        if isinstance(row, dict)
    }


def _selected_stock_options(options, selections):
    """Use the same tracked-option selection for reservation and its display."""
    selected_keys = _selected_option_keys(selections)
    known_keys = {((group.get("name") or "").strip(), (option.get("name") or "").strip())
                  for group in options if isinstance(group, dict)
                  for option in group.get("options") or [] if isinstance(option, dict)}
    if not selected_keys.issubset(known_keys):
        return []
    stock_options = []
    selected_options = []
    for group in options:
        if not isinstance(group, dict):
            continue
        group_name = (group.get("name") or "").strip()
        for option in group.get("options") or []:
            if not isinstance(option, dict) or "stock" not in option:
                continue
            stock_options.append(option)
            option_name = (option.get("name") or "").strip()
            if (group_name, option_name) in selected_keys:
                selected_options.append(option)
    if not selected_options and not selected_keys and len(stock_options) == 1:
        selected_options = stock_options
    return selected_options


def active_inventory_reservations(product=None, *, product_ids=None):
    from api.models import MarketplaceOrder
    from django.db.models import Q
    orders = MarketplaceOrder.objects.filter(
        status__in=(MarketplaceOrder.STATUS_PENDING, MarketplaceOrder.STATUS_PROCESSING,
                    MarketplaceOrder.STATUS_READY_FOR_PICKUP),
        inventory_deducted=True, inventory_restored=False,
    )
    ids = {product.pk} if product is not None else set(product_ids or [])
    query = Q(product_id__in=ids)
    if product is not None:
        query |= Q(customization__bundle_components__contains=[{"product_id": product.pk}])
    elif ids:
        # Holds belong to the purchased snapshot, even if a recipe was repaired
        # outside the normal UI. This is still one batch SQL query.
        for product_id in ids:
            query |= Q(customization__bundle_components__contains=[{"product_id": product_id}])
    for order in orders.filter(query).distinct().values("product_id", "quantity", "customization"):
        allocations = (order["customization"] or {}).get("bundle_components") or []
        if allocations:
            for row in allocations:
                if row["product_id"] in ids:
                    yield {"product_id": row["product_id"], "quantity": order["quantity"] * row["required_quantity"], "customization": {"selections": row["selections"]}}
        elif order["product_id"] in ids:
            yield order


def validate_inventory_option_changes(product, new_options):
    """Preserve the names used to identify actual reserved stock."""
    old_items = product_variant_items(product)
    new_items = flatten_customization_inventory(new_options) if customization_has_stock_tracking(new_options) else []
    from api.models import BundleComponent
    references = list(BundleComponent.objects.filter(product_id=product.pk, bundle__is_archived=False).values_list("selections", flat=True))
    if references:
        new_keys = {(item["group_name"], item["variant_name"]) for item in new_items}
        for selections in references:
            held_keys = _selected_option_keys(selections)
            if bool(old_items) != bool(new_items) or (old_items and not held_keys.issubset(new_keys)):
                raise InventoryStockError("Update the referencing bundle components before removing or renaming their variants.")
    orders = list(active_inventory_reservations(product))
    if not orders:
        return
    if bool(old_items) != bool(new_items):
        raise InventoryStockError("Complete or cancel reserved orders before changing the inventory type.")
    new_keys = {(item["group_name"], item["variant_name"]) for item in new_items}
    if old_items:
        from .customization import parse_order_selections
        for order in orders:
            selected = _selected_stock_options(product.customization_options, parse_order_selections(order["customization"]))
            held_keys = {(group.get("name") or "", option.get("name") or "")
                         for group in product.customization_options for option in group.get("options") or []
                         if any(option is held for held in selected)}
            if not held_keys or not held_keys.issubset(new_keys):
                raise InventoryStockError("Variants with reserved stock cannot be removed or renamed. Complete or cancel their orders first.")


def get_product_inventory_snapshot(product, *, reservation_rows=None):
    """Saved stock is already available; reconstruct on-hand from real holds."""
    # Local imports avoid a cycle: Product itself imports this inventory service.
    from .customization import parse_order_selections
    from decimal import Decimal
    from django.db.models import prefetch_related_objects
    prefetch_related_objects([product], "inventory_skus")
    from .bundles import is_bundle, bundle_inventory
    if is_bundle(product):
        detail = bundle_inventory(product)
        state = INVENTORY_STATUS_IN_STOCK if detail["available"] > 0 else INVENTORY_STATUS_OUT_OF_STOCK
        return {"sku": inventory_sku(product), "on_hand": None, "reserved": None, "available": detail["available"],
                "low_stock_threshold": None, "variant_thresholds": [], "derived": True,
                "components": detail["components"], "status": state, "status_label": INVENTORY_STATUS_LABELS[state]}

    available = get_product_total_stock(product)
    orders = active_inventory_reservations(product) if reservation_rows is None else reservation_rows
    options = product.customization_options or []
    variants = product_variant_items(product)
    tracks_options = bool(variants)
    option_keys = {
        ((group.get("name") or "").strip(), (option.get("name") or "").strip())
        for group in options if isinstance(group, dict)
        for option in group.get("options") or [] if isinstance(option, dict)
    }
    reserved = 0
    held_by_option = {id(option): 0 for group in options if isinstance(group, dict)
                      for option in group.get("options") or [] if isinstance(option, dict)}
    for order in orders:
        units_per_item = 1
        if tracks_options:
            selections = parse_order_selections(order["customization"])
            if not _selected_option_keys(selections).issubset(option_keys):
                return None  # Renamed/deleted selections cannot establish a truthful hold.
            units_per_item = len(_selected_stock_options(options, selections))
            if not units_per_item:
                return None
            for option in _selected_stock_options(options, selections):
                held_by_option[id(option)] += order["quantity"]
        reserved += order["quantity"] * units_per_item
    status = get_product_quantity_status(product)
    variant_rows = []
    for item in variants:
        group_index, option_index = map(int, item["variant_key"].split(":"))
        option = options[group_index]["options"][option_index]
        held = held_by_option[id(option)]
        state = get_inventory_status(stock=item["stock"], threshold=item["low_stock_threshold"])
        variant_rows.append({"name": item["variant_name"], "group": item["group_name"],
                             "sku": inventory_sku(product, group=item["group_name"], variant=item["variant_name"]),
                             "variant_key": item["variant_key"], "available": item["stock"],
                             "on_hand": item["stock"] + held, "reserved": held,
                             "threshold": item["low_stock_threshold"], "status": state,
                             "status_label": get_inventory_status_label(state),
                             "price": str((Decimal(product.price or 0) + Decimal(str(option.get("extra_price") or 0))).quantize(Decimal("0.01"))),
                             "image_url": option.get("image") or ""})
    return {
        "on_hand": available + reserved,
        "sku": inventory_sku(product),
        "reserved": reserved,
        "available": available,
        "low_stock_threshold": None if variants else low_stock_threshold(product),
        "variant_thresholds": variant_rows,
        "status": status,
        "status_label": INVENTORY_STATUS_LABELS[status],
    }


def inventory_sku(product, *, group="", variant=""):
    """Read the dedicated identity, independently of Product ID/product_code."""
    identity = next((row for row in product.inventory_skus.all()
                     if (row.group_name, row.variant_name) == (group, variant)), None)
    return identity.code if identity else "Unassigned"


def build_inventory_table(products):
    """Expand authorized products with batched holds and existing seller metadata."""
    from collections import defaultdict
    from django.db.models import QuerySet, prefetch_related_objects
    from django.urls import reverse
    from urllib.parse import urlencode
    from .bundles import prime_bundle_inventory
    if isinstance(products, QuerySet):
        products = products.select_related("mobile_seller", "mobile_seller__department", "mobile_seller__major", "seller", "seller__department", "seller__major", "department", "major").prefetch_related("inventory_skus")
    else:
        products = list(products)
    products = prime_bundle_inventory(products)
    holds = defaultdict(list)
    for row in active_inventory_reservations(product_ids=[product.pk for product in products]):
        holds[row["product_id"]].append(row)
    rows = []
    for product in products:
        snapshot = get_product_inventory_snapshot(product, reservation_rows=holds[product.pk])
        variants = product_variant_items(product)
        parent_image = reverse("product_image", args=[product.pk]) if product.get_image_list() else ""
        if snapshot:
            items = snapshot["variant_thresholds"] or [{**snapshot, "name": "", "group": "", "price": str(product.price), "image_url": ""}]
        else:
            items = [{"name": item["variant_name"], "group": item["group_name"],
                      "available": item["stock"], "threshold": item["low_stock_threshold"], "image_url": item.get("image_url") or "",
                      "on_hand": None, "reserved": None, "status": "unavailable",
                      "status_label": "Unavailable"} for item in variants]
        for item in items:
            identity = next((row for row in product.inventory_skus.all()
                             if (row.group_name, row.variant_name) == (item["group"], item["name"])), None)
            department = product.department or product.owner.department
            from accounts.academic import product_academic
            rows.append({**item, "product_id": product.pk, "product_name": product.name,
                         "thumbnail_url": item.get("image_url") or parent_image,
                         "thumbnail_fallback_url": parent_image if item.get("image_url") else "",
                         **product_academic(product),
                         "sku": inventory_sku(product, group=item["group"], variant=item["name"]),
                         "sku_id": identity.pk if identity else None,
                         "seller_name": product.owner.get_full_name().strip() or product.owner.username,
                         "seller_id": product.owner_key, "category": product.category,
                         "department_name": str(department) if department else "Not assigned",
                         "department_id": department.pk if department else None,
                         "updated_at": product.updated_at,
                         "status_label": "Available" if item.get("derived") and item["status"] == INVENTORY_STATUS_IN_STOCK else item["status_label"],
                         "threshold": item.get("threshold", item.get("low_stock_threshold")),
                         "details_url": reverse("admin_products_page") + "?" + urlencode({"product_id": product.pk})})
    return rows


def adjust_product_stock(product, selections, quantity, *, restore=False):
    """Reserve or restore simple and option-level product inventory in place."""
    quantity = int(quantity)
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")
    from .bundles import is_bundle
    if is_bundle(product):
        raise InsufficientStockError("Bundle inventory must be reserved or restored through its components.")

    product._inventory_kind = "release" if restore else "reservation"
    if not getattr(product, "_inventory_actor", ""):
        product._inventory_actor = "System"

    options = product.customization_options or []
    if customization_has_stock_tracking(options):
        selected_options = _selected_stock_options(options, selections)
        if not selected_options:
            raise InsufficientStockError("Select an available product option.")

        if not restore:
            for option in selected_options:
                available = max(int(option.get("stock", 0) or 0), 0)
                if available < quantity:
                    name = (option.get("name") or "Selected option").strip()
                    raise InsufficientStockError(
                        f"{name} only has {available} item(s) available."
                    )

        direction = 1 if restore else -1
        for option in selected_options:
            current = max(int(option.get("stock", 0) or 0), 0)
            option["stock"] = max(current + (direction * quantity), 0)

        product.customization_options = options
        sync_product_inventory_fields(product)
        return

    current = max(int(product.stock or 0), 0)
    if not restore and current < quantity:
        raise InsufficientStockError(
            f"Only {current} item(s) are available for this product."
        )
    product.stock = current + quantity if restore else current - quantity


def is_marketplace_available(product, today=None):
    today = today or timezone.localdate()
    status = get_product_inventory_status(product, today=today)
    if status in {
        INVENTORY_STATUS_OUT_OF_STOCK,
        INVENTORY_STATUS_EXPIRED,
    }:
        return False
    return product.approval_status == product.STATUS_APPROVED


def parse_expiry_date(value):
    raw = (value or "").strip()
    if not raw:
        return None
    return date.fromisoformat(raw)


def suggested_expiry_date(days=None):
    days = days if days is not None else expiry_warning_days()
    return timezone.localdate() + timedelta(days=days)
