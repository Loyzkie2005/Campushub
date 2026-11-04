"""Read-only checkout pricing using the same variant/bundle inventory rules as orders."""
from decimal import Decimal
from collections import defaultdict
from api.models import Product, SellerRequest
from .bundles import component_inventory, describe_bundle, is_bundle


def quote_cart(items, *, buyer=None):
    """Combine shared SKU/component demands so cart lines cannot overpromise stock."""
    from .bundles import recipe_rows
    from .inventory import _selected_stock_options, product_variant_items
    demands, stocks, quotes = defaultdict(int), {}, []

    def demand(product, selections, quantity):
        info = component_inventory(product, selections)
        if product_variant_items(product):
            for option in _selected_stock_options(product.customization_options, info["selections"]):
                group = next(group["name"] for group in product.customization_options if any(opt is option for opt in group["options"]))
                key = (product.pk, group, option["name"])
                demands[key] += quantity
                stocks[key] = int(option["stock"]) if info["available"] else 0
        else:
            key = (product.pk, "", "")
            demands[key] += quantity
            stocks[key] = info["available"]

    for item in items:
        if buyer is not None and isinstance(item, dict):
            from .product_ownership import require_other_owner
            candidate = Product.objects.filter(pk=item.get('product_id')).first()
            if candidate is not None:
                require_other_owner(buyer, candidate)
        quote = quote_item(item)
        product = Product.objects.select_related("seller", "mobile_seller").get(pk=quote["product_id"])
        quotes.append(quote)
        if is_bundle(product):
            for row in recipe_rows(product):
                demand(row.product, row.selections, row.required_quantity * quote["quantity"])
        else:
            demand(product, item.get("customization") or [], quote["quantity"])
    if any(quantity > stocks[key] for key, quantity in demands.items()):
        raise ValueError("Selected cart items share insufficient stock. Reduce quantities and retry.")
    return quotes


def supports_delivery(product, *, lock=False):
    requests = SellerRequest.objects.filter(
        **({"mobile_user_id": product.mobile_seller_id} if product.mobile_seller_id else {"user_id": product.seller_id}))
    if lock:
        requests = requests.select_for_update()
    application = requests.order_by("-created_at", "-pk").first()
    return bool(application and application.status == "approved" and not application.is_suspended
                and application.seller_delivery_enabled and product.owner.is_active)


def quote_item(data, product=None):
    if not isinstance(data, dict):
        raise ValueError("Send a checkout item.")
    quantity = data.get("quantity")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 2147483647:
        raise ValueError("Quantity must be a positive whole number.")
    product = product or Product.objects.select_related("seller", "mobile_seller").filter(
        pk=data.get("product_id"), approval_status=Product.STATUS_APPROVED, is_archived=False).first()
    if product is None or not product.owner.is_active:
        raise ValueError("This product is no longer available.")
    if is_bundle(product):
        detail = describe_bundle(product)
        available, unit_price = detail["available"], Decimal(product.price)
    else:
        detail = component_inventory(product, data.get("customization") or [])
        available, unit_price = detail["available"], Decimal(detail["unit_price"])
    if available < quantity:
        raise ValueError(f"{product.name}: only {available} item(s) available.")
    subtotal = (unit_price * quantity).quantize(Decimal("0.01"))
    if not unit_price.is_finite() or unit_price < 0 or subtotal > Decimal("99999999.99"):
        raise ValueError("The final amount is outside the supported order limit.")
    return {"product_id": product.pk, "quantity": quantity, "available": available,
            "unit_price": str(unit_price), "subtotal": str(subtotal),
            "delivery_supported": supports_delivery(product), "delivery_fee": "0.00",
            "total": str(subtotal)}
