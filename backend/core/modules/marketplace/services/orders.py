"""Read-only Orders filters and transaction presentation; stock stays in Inventory."""
import json
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Case, CharField, Count, F, Func, JSONField, Q, Value, When
from django.db.models.functions import Cast, Concat, LPad
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.academic import academic_labels, academic_options, product_academic
from accounts.models import User
from api.models import CampusHubUser, MarketplaceOrder
from .customization import parse_order_selections
from .order_access import admin_order_queryset


def filter_orders(queryset, params):
    """Combine GET filters within an already authorized seller/product scope."""
    values = {name: (params.get(name) or "").strip() for name in
              ("search", "status", "payment", "program", "major", "date", "date_from", "date_to", "fulfillment")}
    error = ""
    if values["fulfillment"]:
        if values["fulfillment"] not in {"pickup", "seller_delivery", "not_recorded"}:
            return queryset.none(), values, "Select a valid fulfillment method."
        queryset = queryset.filter(fulfillment_method="" if values["fulfillment"] == "not_recorded" else values["fulfillment"])
    # Dashboard link selection intersects the already authorized Orders queryset.
    selected_order = (params.get("order") or "").strip()
    if selected_order:
        if not selected_order.isdecimal() or len(selected_order) > 18:
            return queryset.none(), values, "Select a valid order."
        queryset = queryset.filter(pk=selected_order)
    for name, choices, field in (("status", MarketplaceOrder.STATUS_CHOICES, "status"),
                                 ("payment", MarketplaceOrder.PAYMENT_STATUS_CHOICES, "payment_status")):
        if values[name]:
            if values[name] not in dict(choices):
                return queryset.none(), values, "Select a valid order or payment status."
            queryset = queryset.filter(**{field: values[name]})
    programs, majors = academic_options()
    program = programs.filter(pk=values["program"]).first() if values["program"].isdigit() else None
    major = majors.filter(pk=values["major"], program=program).first() if values["major"].isdigit() and program else None
    if values["program"] and not program:
        return queryset.none(), values, "Select a valid program."
    if values["major"] and not major:
        return queryset.none(), values, "Select a major belonging to the selected program."
    if program:
        queryset = queryset.filter(Q(product__department=program) |
                                   Q(product__department__isnull=True, product__seller__department=program))
    if major:
        queryset = queryset.filter(Q(product__department__isnull=False, product__major=major) |
                                   Q(product__department__isnull=True, product__seller__major=major))
    if values["search"]:
        term = values["search"]
        # Stored snapshot names remain searchable after a product rename/deletion.
        query = Q(order_code__icontains=term) | Q(buyer_name__icontains=term) | Q(product_name__icontains=term)
        queryset = queryset.annotate(snapshot_item_names=Cast(Func(F("customization"),
            Value("$.items[*].product_name"), function="jsonb_path_query_array", output_field=JSONField()), CharField()))
        query |= Q(snapshot_item_names__icontains=term)
        # Legacy rows without a name snapshot may still resolve a real buyer.
        buyer_match = Q(first_name__icontains=term) | Q(last_name__icontains=term) | Q(username__icontains=term) | Q(full_name__icontains=term)
        for buyer_model in (User, CampusHubUser):
            ids = buyer_model.objects.annotate(full_name=Concat("first_name", Value(" "), "last_name")).filter(buyer_match).values("pk")
            query |= Q(buyer_name="", buyer_user_id__in=ids)
        # SKU is a separate persisted identity, never the Product ID.
        from api.models import InventorySKU
        skus = InventorySKU.objects.filter(product_id__in=queryset.values("product_id"))
        # Match the registry's prefix[-variant]-sequence format in SQL.
        matching_skus = skus.annotate(search_code=Concat("prefix", Value("-"),
            Case(When(variant_code="", then=Value("")), default=Concat("variant_code", Value("-")), output_field=CharField()),
            Case(When(pk__lt=1000, then=LPad(Cast("pk", CharField()), 3, Value("0"))),
                 default=Cast("pk", CharField()), output_field=CharField()))).filter(search_code__icontains=term)
        sku_match = Q(pk__in=[])
        for sku in matching_skus:
            if sku.variant_name:
                sku_match |= Q(product_id=sku.product_id, customization__selections__contains=[
                    {"group": sku.group_name, "option": sku.variant_name}])
            else:
                sku_match |= Q(product_id=sku.product_id)
        queryset = queryset.filter(query | sku_match)
    today = timezone.localdate()
    start = end = None
    preset = values["date"]
    if preset == "today":
        start = end = today
    elif preset in {"7days", "30days"}:
        start, end = today - timedelta(days=int(preset[:-4]) - 1), today
    elif preset == "month":
        start, end = today.replace(day=1), today
    elif preset == "previous_month":
        end = today.replace(day=1) - timedelta(days=1)
        start = end.replace(day=1)
    elif preset == "custom":
        try:
            start, end = parse_date(values["date_from"]), parse_date(values["date_to"])
        except ValueError:
            start = end = None
        if not start or not end or start > end:
            return queryset.none(), values, "Select a valid start and end date; the start must not be after the end."
    elif preset:
        return queryset.none(), values, "Select a valid date range."
    if start and end:
        # Local midnight boundaries include the entire final day without DB date casts.
        first = timezone.make_aware(datetime.combine(start, time.min))
        after_last = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
        queryset = queryset.filter(created_at__gte=first, created_at__lt=after_last)
    return queryset, values, error


def _money(value):
    try:
        amount = Decimal(str(value))
        return str(amount.quantize(Decimal("0.01"))) if amount.is_finite() else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def order_items(order):
    """Read checkout snapshots, never today's product prices or bundle components."""
    data = order.customization if isinstance(order.customization, dict) else {}
    raw_items = data.get("items")
    if data.get("bundle_components") or not isinstance(raw_items, list) or not raw_items:
        raw_items = [{"product_name": order.product_name, "variant": order.option,
                      "quantity": order.quantity, "unit_price": str(order.unit_price),
                      "subtotal": str(order.unit_price * order.quantity)}]
    identities = {(sku.group_name, sku.variant_name): sku.code
                  for sku in order.product.inventory_skus.all()} if order.product_id else {}
    selected = parse_order_selections(data)
    selected_codes = [identities[(row["group"], row["option"])] for row in selected
                      if (row["group"], row["option"]) in identities]
    # A bundle is one purchased item, using its own SKU, not component SKUs.
    if data.get("bundle_components"):
        selected_codes = []
    if not selected_codes and not selected:
        if order.option and not data.get("bundle_components"):
            selected_codes = [code for (_, name), code in identities.items() if name == order.option]
        elif ("", "") in identities:
            selected_codes = [identities[("", "")]]
    items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        try:
            qty = int(raw.get("quantity"))
            qty = qty if qty > 0 else None
        except (TypeError, ValueError):
            qty = None
        price = _money(raw.get("unit_price"))
        subtotal = _money(raw.get("subtotal"))
        if subtotal is None and qty and price is not None:
            subtotal = _money(Decimal(price) * qty)
        items.append({"product_name": raw.get("product_name") or order.product_name,
                      "variant": raw.get("variant") or raw.get("option") or order.option or "Not applicable",
                      "sku": raw.get("sku") or (", ".join(selected_codes) if len(raw_items) == 1 else "Not recorded"),
                      "quantity": qty, "unit_price": price, "subtotal": subtotal})
    return items


def _date(value):
    return timezone.localtime(value).strftime("%b %d, %Y at %I:%M %p") if value else ""


def decorate_orders(orders):
    """Batch related buyers/SKUs/history for one page; never write on a GET."""
    ids = {order.buyer_user_id for order in orders if order.buyer_user_id}
    web = {u.pk: u for u in User.objects.filter(pk__in=ids).select_related("department", "major")}
    mobile = {u.pk: u for u in CampusHubUser.objects.filter(pk__in=ids).select_related("department", "major")}
    for order in orders:
        from .fulfillment import presentation
        order.fulfillment = presentation(order)
        candidates = [u for u in (mobile.get(order.buyer_user_id), web.get(order.buyer_user_id)) if u]
        # Separate legacy user ID namespaces can overlap. Prefer a matching saved email.
        buyer = next((u for u in candidates if order.buyer_email and u.email == order.buyer_email),
                     candidates[0] if len(candidates) == 1 else None)
        order.display_buyer_name = order.buyer_name or (
            (f"{buyer.first_name} {buyer.last_name}".strip() or buyer.username) if buyer else "Unknown customer")
        order.display_buyer_email = order.buyer_email or (buyer.email if buyer else "")
        order.display_buyer_phone = buyer.contact_number if buyer else ""
        order.buyer_user_type = getattr(buyer, "user_type", "") or getattr(buyer, "role", "") if buyer else ""
        order.buyer_academic = academic_labels(buyer.department, buyer.major) if buyer else academic_labels(None)
        order.seller_academic = product_academic(order.product) if order.product_id else academic_labels(None)
        order.display_seller_name = order.seller_name or (
            order.product.owner.get_full_name() or order.product.owner.username if order.product_id else "Not recorded")
        items = order_items(order)
        order.items_json = json.dumps(items)
        first = items[0]["product_name"] if items else order.product_name
        order.display_items = f"{first} + {len(items)-1} more" if len(items) > 1 else first
        order.display_qty = sum(i["quantity"] or 0 for i in items) if items else order.quantity
        order.items_subtotal = _money(sum(Decimal(i["subtotal"]) for i in items)) if items and all(i["subtotal"] is not None for i in items) else ""
        history = [{"new_status_label": "Created", "changed_by": order.display_buyer_name,
                    "created_at": _date(order.created_at), "notes": ""}]
        for event in sorted(order.status_history.all(), key=lambda h: (h.created_at, h.pk)):
            history.append({"new_status_label": "Ready for Seller Delivery" if order.fulfillment_method == "seller_delivery" and event.new_status == "ready_for_pickup" else dict(order.STATUS_CHOICES).get(event.new_status, event.new_status),
                            "changed_by": event.changed_by or "Not recorded", "notes": event.notes,
                            "created_at": _date(event.created_at)})
        order.status_history_json = json.dumps(history)


def orders_page_context(user, params):
    """Authorized base -> combined filters -> all matching KPI counts -> page rows."""
    base = admin_order_queryset(user)
    has_orders = base.exists()
    filtered, values, error = filter_orders(base, params)
    stats = filtered.aggregate(total=Count("pk"), **{
        status: Count("pk", filter=Q(status=status)) for status, _ in MarketplaceOrder.STATUS_CHOICES})
    stats["ready_for_pickup"] = filtered.filter(status="ready_for_pickup", fulfillment_method="pickup").count()
    page = Paginator(filtered.select_related("product__mobile_seller__department", "product__mobile_seller__major", "product__seller__department", "product__seller__major",
                     "product__department", "product__major").prefetch_related("status_history", "product__inventory_skus")
                     .order_by("-created_at", "-pk"), 10).get_page(params.get("page"))
    orders = list(page.object_list)
    decorate_orders(orders)
    programs, majors = academic_options()
    remaining = params.copy()
    remaining.pop("page", None)
    return {"orders": orders, "order_stats": stats, "page_obj": page, "filters": values,
            "filter_error": error, "has_orders": has_orders, "programs": programs, "majors": majors,
            "query_without_page": remaining.urlencode()}
