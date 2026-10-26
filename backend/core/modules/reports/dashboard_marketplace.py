"""High-level marketplace summaries from completed paid transaction querysets."""
from decimal import Decimal
from math import cos, radians, sin
from django.db.models import Case, CharField, Count, Max, Sum, Value, When
from django.db.models.functions import Cast, Coalesce, Concat, NullIf, Trim
from django.urls import reverse
from django.utils import timezone

from api.models import Product


def _recent_order_items(order):
    """Purchased units from stored checkout items; a bundle remains one sellable item."""
    data = order.customization if isinstance(order.customization, dict) else {}
    items = data.get("items")
    if data.get("bundle_components") or not isinstance(items, list) or not items:
        return order.quantity, False
    total = 0
    for item in items:
        value = item.get("quantity") if isinstance(item, dict) else None
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            return None, len(items) > 1
        if isinstance(value, str) and (not value.strip().isascii() or not value.strip().isdigit()):
            return None, len(items) > 1
        try:
            quantity = int(value)
        except (ValueError, OverflowError):
            return None, len(items) > 1
        if quantity < 0:
            return None, len(items) > 1
        total += quantity
    return total, len(items) > 1


def _recent_order_seller(order, ambiguous_items):
    """Do not assign a primary-product owner to an unowned legacy item array."""
    if ambiguous_items:
        return "Not fully recorded"
    snapshot = (order.seller_name or "").strip()
    if snapshot:
        return snapshot
    product = order.product if order.product_id else None
    owner = (product.mobile_seller if product.mobile_seller_id else product.seller) if product else None
    return ((owner.get_full_name() or owner.username).strip() if owner else "") or "Not recorded"


def recent_marketplace_orders(orders, limit=6):
    """One bounded snapshot query, shared by initial dashboard and refresh."""
    from modules.marketplace.services.fulfillment import presentation
    result = []
    for order in orders.select_related("product__seller", "product__mobile_seller").order_by("-created_at", "-pk")[:limit]:
        has_image = bool(order.product_id and order.product.get_image_list())
        item_count, ambiguous_items = _recent_order_items(order)
        result.append({
            "id": order.pk, "code": order.order_code or f"#{order.pk}",
            "url": reverse("admin_orders_page") + f"?order={order.pk}",
            "buyer_name": (order.buyer_name or "").strip() or "—",
            "product_name": order.product_name, "quantity": order.quantity,
            "seller_name": _recent_order_seller(order, ambiguous_items), "item_count": item_count,
            "total": f"{order.total_price:,.2f}",
            "status": order.get_status_display(), "status_key": order.status,
            "payment_status": order.get_payment_status_display(), "payment_key": order.payment_status,
            "fulfillment": presentation(order),
            "date": timezone.localtime(order.created_at).strftime("%b %d, %Y") if order.created_at else "—",
            "image_url": reverse("product_image", args=[order.product_id]) if has_image else "",
        })
    return result


def top_selling_products(orders, limit=5):
    # One MarketplaceOrder is a sellable-product transaction, with customization
    # on that row. Group variants under their parent ID; don't expand bundle parts.
    rows = orders.annotate(product_identity=Case(
        When(product_id__isnull=False, then=Concat(Value("product:"), Cast("product_id", CharField()))),
        default=Concat(Value("historical:"), "product_name"), output_field=CharField(),
    )).values("product_identity", "product_id").annotate(
        historical_name=Max("product_name"), current_name=Max("product__name"),
        historical_seller=Max("seller_name"),
        current_category=Max("product__category"), historical_category=Max("category"),
        current_image=Max("product__image_url"), units_sold=Sum("quantity"), sales_sum=Sum("total_price"),
    ).order_by("-units_sold", "-sales_sum", "product_identity")[:limit]
    products = []
    for rank, row in enumerate(rows, 1):
        product_id = row["product_id"]
        has_image = bool(product_id and Product(image_url=row["current_image"] or "").get_image_list())
        products.append({"rank": rank, "id": product_id,
                         "product_name": row["current_name"] or row["historical_name"],
                         "category": (row["current_category"] or "").strip() or (row["historical_category"] or "").strip() or "Uncategorized",
                         "seller_name": row["historical_seller"] or "Not Assigned",
                         "units_sold": row["units_sold"] or 0, "sales": f"{row['sales_sum']:,.2f}",
                         "image_url": reverse("product_image", args=[product_id]) if has_image else "",
                         "product_url": reverse("admin_products_page") + f"?product_id={product_id}" if product_id else ""})
    return products


def top_selling_product(orders):
    """Compatibility for existing consumers of the single-product summary."""
    products = top_selling_products(orders, limit=1)
    return products[0] if products else None


def sales_by_product_category(orders):
    # Prefer the category recorded on the sale. Older rows without a snapshot
    # can use their surviving product's category; deleted/blank rows stay honest.
    rows = list(orders.annotate(category_name=Coalesce(
        NullIf(Trim("category"), Value("")),
        NullIf(Trim("product__category"), Value("")), Value("Uncategorized"),
    )).values("category_name").annotate(
        count=Count("pk"), units_sold=Sum("quantity"), sales=Sum("total_price"),
    ).order_by("-sales", "category_name"))
    total = sum(row["count"] for row in rows)
    total_sales = sum((row["sales"] or Decimal("0") for row in rows), Decimal("0"))
    colors = ("#1A1851", "#FCB315", "#69717E", "#939AA5", "#BDC2CB", "#E0E3E8")
    categories = []
    offset = Decimal("0")
    for index, row in enumerate(rows):
        share = row["sales"] / total_sales * 100 if total_sales > 0 else Decimal("0")
        midpoint = radians(float(offset + share / 2) * 3.6 - 90)
        categories.append({"name": row["category_name"], "count": row["count"],
                           "units_sold": row["units_sold"], "sales": f"{row['sales']:,.2f}",
                           "percentage": round(float(share), 1),
                           "chart": {"color": colors[min(index, len(colors) - 1)],
                                     "share": round(float(share), 6), "offset": round(float(-offset), 6),
                                     "label_x": round(120 + 88 * cos(midpoint), 3),
                                     "label_y": round(120 + 88 * sin(midpoint), 3),
                                     "label_color": "#FFFFFF" if index in (0, 2, 3) else "#1A1851"}})
        offset += share
    return {"total": total, "is_snapshot": False, "kind": "completed_paid_category_sales",
            "share_basis": "completed_paid_sales_amount", "total_sales": f"{total_sales:,.2f}",
            "categories": categories}


def category_sales_chart(summary, limit=5):
    """Bound an existing revenue summary for a donut; no extra query or eligibility rule."""
    limit = max(1, min(limit, 5))
    total = Decimal(summary["total_sales"].replace(",", ""))
    rows = [{"name": row["name"], "amount": Decimal(row["sales"].replace(",", ""))}
            for row in summary["categories"] if Decimal(row["sales"].replace(",", "")) > 0]
    if len(rows) > limit:
        # Reserve a single Others label even when the catalog contains that name.
        named = [row for row in rows if row["name"] != "Others"][:limit]
        kept = {row["name"] for row in named}
        remainder = sum((row["amount"] for row in rows if row["name"] not in kept), Decimal("0"))
        rows = named + [{"name": "Others", "amount": remainder}]
    colors = ("#1A1851", "#FCB316", "#69717E", "#939AA5", "#BDC2CB", "#E0E3E8")
    result = [{"name": row["name"], "sales": f"{row['amount']:,.2f}",
               "value": float(row["amount"]), "percentage": round(float(row["amount"] / total * 100), 1),
               "color": colors[index]} for index, row in enumerate(rows)] if total > 0 else []
    return {"total_sales": summary["total_sales"], "has_sales": total > 0, "categories": result,
            "labels": [row["name"] for row in result], "values": [row["value"] for row in result],
            "percentages": [row["percentage"] for row in result], "colors": [row["color"] for row in result]}
