"""Component recipes, derived availability, and exact inventory reservations.

Bundle orders remain one MarketplaceOrder. Its existing customization JSON stores
the purchased recipe so cancellations never restore a subsequently edited recipe.
"""
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch, QuerySet, prefetch_related_objects
from django.utils import timezone

from .customization import parse_order_selections, validate_order_selections


class BundleError(ValueError):
    pass


def is_bundle(product):
    return getattr(product, "product_type", "single") == "bundle"


def component_inventory(product, selections):
    """Use exact selected option stock, never the parent sum for a variant SKU."""
    from .inventory import (_selected_stock_options, product_variant_items,
                            get_inventory_status, get_product_total_stock)
    selections = parse_order_selections(selections)
    validated, extra, error = validate_order_selections(product.customization_options or [], selections)
    if error:
        raise BundleError(error)
    price = (product.price + extra).quantize(Decimal("0.01"))
    if product_variant_items(product):
        if not validated:
            raise BundleError(f"Select the exact stock-tracked variant for {product.name}.")
        chosen = _selected_stock_options(product.customization_options, validated)
        if not chosen:
            raise BundleError(f"Select a stock-tracked variant for {product.name}.")
        available = min(max(int(option["stock"]), 0) for option in chosen)
        expired = any(get_inventory_status(stock=option["stock"], category=product.category,
            expiry_date=(timezone.datetime.fromisoformat(option["expiry_date"]).date() if option.get("expiry_date") else None)) == "expired" for option in chosen)
    else:
        if selections and not product.customization_options:
            raise BundleError(f"{product.name} has no variants.")
        available = get_product_total_stock(product)
        expired = get_inventory_status(stock=available, expiry_date=product.expiry_date, category=product.category) == "expired"
    return {"available": 0 if expired else available, "unit_price": str(price),
            "selections": validated, "variant": ", ".join(row["option"] for row in validated)}


def eligible_component(product, seller_id):
    return (not is_bundle(product) and product.owner_key == seller_id
            and product.approval_status == product.STATUS_APPROVED
            and not product.is_archived and product.owner.is_active)


def recipe_rows(bundle):
    rows = bundle.bundle_components.all()
    if "bundle_components" not in getattr(bundle, "_prefetched_objects_cache", {}):
        rows = rows.select_related("product", "product__seller")
    return list(rows)


def describe_bundle(bundle, rows=None):
    """Current price/availability, including shared variant demands across rows."""
    from .inventory import _selected_stock_options, product_variant_items
    rows = recipe_rows(bundle) if rows is None else rows
    demands, stocks = defaultdict(int), {}
    components = []
    regular = Decimal("0.00")
    regular_known = True
    valid = bool(rows)
    for row in rows:
        product = row.product
        try:
            info = component_inventory(product, row.selections)
        except (BundleError, ValueError, TypeError):
            info = {"available": 0, "unit_price": None, "selections": row.selections, "variant": "Unavailable selection"}
            valid = False
            regular_known = False
        if not eligible_component(product, bundle.owner_key):
            info["available"] = 0
            valid = False
        if product_variant_items(product):
            for option in _selected_stock_options(product.customization_options, info["selections"]):
                group_name = next(group["name"] for group in product.customization_options if any(opt is option for opt in group["options"]))
                key = (product.pk, group_name, option["name"])
                demands[key] += row.required_quantity
                stocks[key] = 0 if info["available"] <= 0 else int(option["stock"])
        else:
            key = (product.pk, "", "")
            demands[key] += row.required_quantity
            stocks[key] = info["available"]
        subtotal = Decimal(info["unit_price"]) * row.required_quantity if info["unit_price"] is not None else None
        if subtotal is not None:
            regular += subtotal
        components.append({"product_id": product.pk, "product_name": product.name,
            "required_quantity": row.required_quantity, **info, "subtotal": str(subtotal.quantize(Decimal("0.01"))) if subtotal is not None else None})
    availability = min((stocks[key] // quantity for key, quantity in demands.items()), default=0) if valid else 0
    return {"available": availability, "regular_price": str(regular.quantize(Decimal("0.01"))) if regular_known else None,
            "bundle_price": str(bundle.price), "savings": str((regular - bundle.price).quantize(Decimal("0.01"))) if regular_known else None, "components": components}


def bundle_inventory(bundle):
    # Primed values are local to the current read request, never global stock caches.
    return getattr(bundle, "_bundle_inventory_data", None) or describe_bundle(bundle)


def prime_bundle_inventory(products):
    """Batch-load recipes/components for catalog and reporting reads."""
    from api.models import BundleComponent
    from accounts.models import User
    if isinstance(products, QuerySet):
        products = products.select_related("mobile_seller", "mobile_seller__department", "mobile_seller__major", "seller", "seller__department", "seller__major", "department", "major").prefetch_related("inventory_skus")
    products = list(products)
    # SKU and academic labels are serialized for every product. Load their
    # relations once, rather than issuing another query for each table row.
    prefetch_related_objects(products, Prefetch("seller", queryset=User.objects.select_related("department", "major")),
                             "department", "major", "inventory_skus")
    bundles = [product for product in products if is_bundle(product)]
    if bundles:
        prefetch_related_objects(bundles, Prefetch("bundle_components",
            queryset=BundleComponent.objects.select_related("product", "product__seller")))
        for bundle in bundles:
            bundle._bundle_inventory_data = describe_bundle(bundle)
    return products


@transaction.atomic
def validate_recipe(raw, seller_id, *, bundle_id=None):
    from api.models import Product
    from .inventory import validate_stock_quantity, InventoryStockError
    bundle_id = int(bundle_id) if bundle_id else None
    if not isinstance(raw, list) or not raw:
        raise BundleError("Add at least one bundle component.")
    if len(raw) > 50:
        raise BundleError("A bundle can contain up to 50 components.")
    parsed = []
    for item in raw:
        if not isinstance(item, dict):
            raise BundleError("Invalid bundle component.")
        try:
            product_id = validate_stock_quantity(item.get("product_id"))
            quantity = validate_stock_quantity(item.get("required_quantity"))
        except InventoryStockError as exc:
            raise BundleError("Choose a valid product and enter a positive whole Required Quantity.") from exc
        if quantity < 1:
            raise BundleError("Required Quantity must be at least 1.")
        parsed.append((product_id, quantity, item.get("selections") or []))
    products = {product.pk: product for product in Product.objects.select_for_update(of=("self",)).select_related("seller").filter(pk__in=[row[0] for row in parsed]).order_by("pk")}
    result, seen = [], set()
    for product_id, quantity, selections in parsed:
        product = products.get(product_id)
        if product is None or product_id == bundle_id or not eligible_component(product, seller_id):
            raise BundleError("Components must be approved, active single products from the same product owner.")
        info = component_inventory(product, selections)
        key = (product_id, tuple(sorted((row["group"], row["option"]) for row in info["selections"])))
        if key in seen:
            raise BundleError("Combine duplicate product/variant quantities into one component row.")
        seen.add(key)
        if info["available"] < quantity:
            raise BundleError(f"{product.name} does not have enough available stock for one bundle.")
        result.append({"product": product, "required_quantity": quantity, "selections": info["selections"]})
    # Different selected combinations can share the same tracked inventory pool.
    probe = Product(mobile_seller_id=int(seller_id.split(":", 1)[1]), price=0, product_type=Product.TYPE_BUNDLE) if isinstance(seller_id, str) and seller_id.startswith("mobile:") else Product(seller_id=seller_id, price=0, product_type=Product.TYPE_BUNDLE)
    from types import SimpleNamespace
    if describe_bundle(probe, [SimpleNamespace(**row) for row in result])["available"] < 1:
        raise BundleError("The selected components share insufficient stock for one bundle.")
    return result


@transaction.atomic
def reserve_bundle(bundle, quantity):
    """Lock all component products by ID; validate every demand before writing."""
    from api.models import Product
    from .inventory import adjust_product_stock, InsufficientStockError
    if quantity < 1:
        raise InsufficientStockError("Bundle quantity must be at least 1.")
    recipe = recipe_rows(bundle)
    locked = {product.pk: product for product in Product.objects.select_for_update(of=("self",)).select_related("seller").filter(pk__in=[row.product_id for row in recipe]).order_by("pk")}
    for row in recipe:
        row.product = locked[row.product_id]
    detail = describe_bundle(bundle, recipe)
    if detail["available"] < quantity:
        raise InsufficientStockError("The bundle components do not have enough available stock.")
    for row in recipe:
        adjust_product_stock(row.product, row.selections, row.required_quantity * quantity)
    for product in locked.values():
        product.save(update_fields=["stock", "customization_options", "updated_at"])
    bundle._inventory_movement_ids = [pk for product in locked.values() for pk in getattr(product, "_inventory_movement_ids", [])]
    bundle._bundle_inventory_data = describe_bundle(bundle, recipe)
    # Immutable order snapshot: no new sellable order rows or analytics items.
    return {"bundle_components": detail["components"], "regular_price": detail["regular_price"], "summary": "Combo / Bundle Product"}


@transaction.atomic
def restore_bundle(order, actor=""):
    from api.models import Product
    from .inventory import adjust_product_stock, InsufficientStockError
    rows = (order.customization or {}).get("bundle_components") or []
    if not rows:
        raise InsufficientStockError("The original bundle reservation is unavailable.")
    locked = {product.pk: product for product in Product.objects.select_for_update(of=("self",)).filter(pk__in=[row["product_id"] for row in rows]).order_by("pk")}
    if len(locked) != len({row["product_id"] for row in rows}):
        raise InsufficientStockError("An original bundle component is unavailable; reconcile the order before cancellation.")
    for row in rows:
        locked[row["product_id"]]._inventory_order_id = order.pk
        locked[row["product_id"]]._inventory_actor = actor or "System"
        adjust_product_stock(locked[row["product_id"]], row["selections"], row["required_quantity"] * order.quantity, restore=True)
    for product in locked.values():
        product.save(update_fields=["stock", "customization_options", "updated_at"])
