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


def low_stock_threshold():
    return int(getattr(settings, "CAMPUSHUB_LOW_STOCK_THRESHOLD", 5))


def expiry_warning_days():
    return int(getattr(settings, "CAMPUSHUB_EXPIRY_WARNING_DAYS", 7))


def is_perishable_category(category):
    return (category or "").strip() in PERISHABLE_CATEGORIES


def get_inventory_status(*, stock, expiry_date=None, category=None, today=None):
    today = today or timezone.localdate()
    threshold = low_stock_threshold()
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
    for group in customization_options or []:
        if not isinstance(group, dict):
            continue
        for opt in group.get("options") or []:
            if not isinstance(opt, dict):
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
            items.append({"stock": stock, "expiry_date": expiry_date})
    return items


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
        )
        for item in option_items
    ]
    stocks = [item["stock"] for item in option_items]

    if all(stock <= 0 for stock in stocks):
        return INVENTORY_STATUS_OUT_OF_STOCK

    if any(stock <= 0 for stock in stocks) and any(stock > 0 for stock in stocks):
        worst = _worst_inventory_status(statuses)
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
        )
    items = product_variant_items(product)
    if items:
        return get_availability_from_options(items, product.category, today=today)
    return get_inventory_status(
        stock=product.stock,
        expiry_date=product.expiry_date if is_perishable_category(product.category) else None,
        category=product.category,
        today=today,
    )


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


def adjust_product_stock(product, selections, quantity, *, restore=False):
    """Reserve or restore simple and option-level product inventory in place."""
    quantity = int(quantity)
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    options = product.customization_options or []
    if product.customization_enabled and customization_has_stock_tracking(options):
        selected_keys = _selected_option_keys(selections)
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

        if not selected_options and len(stock_options) == 1:
            selected_options = stock_options
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
