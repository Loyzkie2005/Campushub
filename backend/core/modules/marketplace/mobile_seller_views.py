"""Mobile seller workspace adapters; canonical inventory/orders/Apriori stay shared."""
import json
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from api.models import Product, SellerBundleSuggestion, MarketplaceOrder
from accounts.activity_logging import log_marketplace_event
from .services.seller_applications import applicant, latest, snapshot
from .services.inventory import build_inventory_table
from .services.bundles import prime_bundle_inventory
from .services.order_access import seller_order_queryset
from .services.fulfillment import presentation
from .services.analytics import valid_sales_queryset, parse_analytics_period, _sales_time_series, _top_products
from .services.bundle_suggestions import build_bundle_suggestions, recommendation_presentation


def approved_seller(request):
    account, source, error = applicant(request, allow_seller=True)
    if error is not None:
        return None, error
    if source != "mobile":
        return None, JsonResponse({"error": "Sign in with your CampusHub mobile account."}, status=403)
    application = latest(account, source)
    if not application or application.status != "approved" or application.is_suspended:
        return None, JsonResponse({"error": "Approved active seller access is required."}, status=403)
    return account, None


def live_suggestions(account):
    result = recommendation_presentation(build_bundle_suggestions(None, mobile_seller=account), limit=3)
    from api.models import BundleRecommendation
    highlighted = set(BundleRecommendation.objects.filter(is_current=True, sent_at__isnull=False,
        product_a__mobile_seller=account, product_b__mobile_seller=account).values_list("product_a_id", "product_b_id"))
    # Highlight only pairs that still qualify under the existing live calculator.
    result["rows"].sort(key=lambda row: pair_key(row) not in highlighted)
    return result


def pair_key(row):
    return tuple(sorted(int(product["id"]) for product in row["products"]))


def saved_pairs(account):
    rows = SellerBundleSuggestion.objects.filter(seller=account, state="saved",
        product_a__mobile_seller=account, product_b__mobile_seller=account).select_related(
        "product_a", "product_b", "product_a__mobile_seller", "product_b__mobile_seller")
    result = []
    for row in rows:
        public_products = []
        for product in (row.product_a, row.product_b):
            images = product.get_image_list()
            public_products.append({"id": product.pk, "name": product.name,
                                    "image_url": images[0] if images else ""})
        result.append({"id": f"{row.product_a_id}|{row.product_b_id}", "seller": account.get_full_name(),
            "products": public_products,
            "product_a": row.product_a.name, "product_b": row.product_b.name,
            "saved": True})
    return result


@never_cache
@require_GET
def workspace(request):
    from api.views import serialize_product
    account, error = approved_seller(request)
    if error is not None:
        return error
    owned = Product.objects.filter(mobile_seller=account).order_by("-submitted_at", "-pk")
    products = prime_bundle_inventory(owned)
    inventory = build_inventory_table([product for product in products if not product.is_archived])
    inventory_fields = ("product_id", "product_name", "name", "sku", "on_hand", "reserved", "available",
                        "threshold", "status", "status_label", "derived", "thumbnail_url")
    rows = [{key: row.get(key) for key in inventory_fields} for row in inventory]
    orders = seller_order_queryset(account)
    period = parse_analytics_period(request.GET)
    sales = valid_sales_queryset().filter(pk__in=orders.values("pk"), analytics_at__date__range=(period.start, period.end))
    amounts = sales.aggregate(revenue=Sum("total_price"), units=Sum("quantity"))
    count = sales.count()
    revenue = amounts["revenue"] or Decimal("0")
    recommendations = live_suggestions(account)
    choices = {(row.product_a_id, row.product_b_id): row.state for row in
               SellerBundleSuggestion.objects.filter(seller=account)}
    recommendations["rows"] = [{**row, "saved": choices.get(pair_key(row)) == "saved"}
        for row in recommendations["rows"] if choices.get(pair_key(row)) != "dismissed"]
    # Do not expose administrative URLs, metrics, thresholds or other sellers.
    public_recommendations = {key: recommendations[key] for key in ("rows", "error", "message", "detail")}
    from .services.orders import order_items
    order_page = Paginator(orders.order_by("-created_at").select_related("product").prefetch_related(
        "product__inventory_skus"), 30).get_page(request.GET.get("orders_page", "1"))
    serialized_orders = [{"id": order.pk, "code": order.order_code or str(order.pk),
        "product_name": order.product_name, "buyer_name": order.buyer_name,
        "quantity": order.quantity, "total": str(order.total_price), "status": presentation(order)["status_label"], "status_key": order.status,
        "payment_status": order.get_payment_status_display(), "created_at": order.created_at,
        "pickup_location": order.pickup_location, "items": order_items(order),
        **presentation(order)}
        for order in order_page]
    public_products = [serialize_product(product, request) for product in products]
    response = JsonResponse({"seller": {**snapshot(account), "year_section": account.year_section},
        "products": public_products, "inventory": rows,
        "overview": {"active_products": sum(product.approval_status == Product.STATUS_APPROVED and not product.is_archived for product in products),
                     "completed_orders": orders.filter(status=MarketplaceOrder.STATUS_COMPLETED).count(),
                     "pending_orders": orders.filter(status="pending").count()},
        "bundle_submissions": [row for row in public_products if row["product_type"] == Product.TYPE_BUNDLE],
        "orders": serialized_orders, "order_count": orders.count(),
        "orders_page": order_page.number, "orders_pages": order_page.paginator.num_pages,
        "recommendations": public_recommendations, "saved_suggestions": saved_pairs(account),
        "analytics": {"period": period.key, "label": period.label,
            "start": str(period.start), "end": str(period.end), "revenue": str(revenue.quantize(Decimal("0.01"))),
            "completed_orders": count, "units_sold": amounts["units"] or 0,
            "average_order_value": str((revenue / count if count else Decimal("0")).quantize(Decimal("0.01"))),
            "trend": _sales_time_series(sales, period, "daily"), "top_products": _top_products(sales)}})
    response["Cache-Control"] = "private, no-store"
    return response


@csrf_exempt
@never_cache
@require_POST
def order_progress(request, order_id):
    account, error = approved_seller(request)
    if error is not None: return error
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict) or set(payload) != {"action"} or not isinstance(payload["action"], str):
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({"error": "Send one fulfillment action; payment updates are not permitted here."}, status=400)
    from api.models import SellerRequest
    from .services.fulfillment import advance
    with transaction.atomic():
        current = latest(account, "mobile")
        if current is None: return JsonResponse({"error": "Approved active seller access is required."}, status=403)
        current = SellerRequest.objects.select_for_update().get(pk=current.pk)
        if current.status != "approved" or current.is_suspended:
            return JsonResponse({"error": "Approved active seller access is required."}, status=403)
        return advance(seller_order_queryset(account), order_id, payload["action"], account.get_full_name() or account.username)


@csrf_exempt
@never_cache
@require_POST
def suggestion_choice(request, pair_id):
    account, error = approved_seller(request)
    if error is not None:
        return error
    try:
        ids = sorted(int(value) for value in pair_id.split("|"))
        if len(ids) != 2 or ids[0] == ids[1]:
            raise ValueError
        action = json.loads(request.body).get("action")
        if action not in {"save", "dismiss", "remove"}:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({"error": "Select a valid suggestion and action."}, status=400)
    owned = Product.objects.filter(pk__in=ids, mobile_seller=account)
    if owned.count() != 2:
        return JsonResponse({"error": "Suggestion not found."}, status=404)
    if action != "remove" and owned.filter(is_archived=False, approval_status="approved").count() != 2:
        return JsonResponse({"error": "This suggestion no longer qualifies."}, status=409)
    if action != "remove":
        result = live_suggestions(account)
        if result["error"]:
            return JsonResponse({"error": "Unable to verify this suggestion. Retry."}, status=503)
        if tuple(ids) not in {pair_key(row) for row in result["rows"]}:
            return JsonResponse({"error": "This suggestion no longer qualifies."}, status=409)
    with transaction.atomic():
        # Serialize against seller approval/suspension changes, as product submission does.
        current = latest(account, "mobile")
        from api.models import SellerRequest
        if current is None:
            return JsonResponse({"error": "Approved active seller access is required."}, status=403)
        current = SellerRequest.objects.select_for_update().get(pk=current.pk)
        if current.status != "approved" or current.is_suspended:
            return JsonResponse({"error": "Approved active seller access is required."}, status=403)
        choices = SellerBundleSuggestion.objects.filter(seller=account, product_a_id=ids[0], product_b_id=ids[1])
        if action == "remove":
            choices.delete()
        else:
            SellerBundleSuggestion.objects.update_or_create(seller=account, product_a_id=ids[0], product_b_id=ids[1],
                defaults={"state": "saved" if action == "save" else "dismissed"})
        log_marketplace_event(request, account=account, source="mobile", activity_type="BUNDLE_SUGGESTION_UPDATED",
            activity={"save": "Bundle suggestion saved.", "dismiss": "Bundle suggestion dismissed.",
                      "remove": "Saved bundle suggestion removed."}[action], metadata={"product_ids": ids})
    return JsonResponse({"message": "Suggestion updated."})
