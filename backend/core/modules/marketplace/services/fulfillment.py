"""Fulfillment events use existing order states; delivery never records payment."""
import json
from functools import wraps
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from api.models import MarketplaceOrder, MarketplaceOrderStatusHistory

ORDER_TRANSITIONS = {
    "pending": {"processing", "cancelled"},
    "processing": {"ready_for_pickup", "cancelled"},
    "ready_for_pickup": {"completed", "cancelled"},
    "completed": set(), "cancelled": set(),
}


def fulfillment_buyer_guard(view):
    """Authenticate new fulfillment requests before any cached idempotency replay."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.method == "POST":
            try: data = json.loads(request.body)
            except (ValueError, TypeError): return view(request, *args, **kwargs)
            if isinstance(data, dict) and data.get("fulfillment_method"):
                if request.headers.get("Authorization"):
                    from api.views import _mobile_user_from_bearer
                    buyer, error = _mobile_user_from_bearer(request)
                    if error is not None: return error
                elif request.user.is_authenticated: buyer = request.user
                else: return JsonResponse({"error": "Sign in before selecting order fulfillment."}, status=401)
                if str(data.get("buyer_user_id")) != str(buyer.pk):
                    return JsonResponse({"error": "The order buyer must match the signed-in account."}, status=403)
                request.fulfillment_buyer = buyer
        return view(request, *args, **kwargs)
    return wrapped


def status_label(order):
    if order.fulfillment_method == "seller_delivery" and order.status == "ready_for_pickup":
        return "Ready for Seller Delivery"
    return order.get_status_display()


def presentation(order):
    delivery = order.fulfillment_method == "seller_delivery"
    progress = ("Cancelled" if order.status == "cancelled" else
        "Delivered" if delivery and order.delivered_at else
        "Out for Seller Delivery" if delivery and order.delivery_started_at else
        "Collected" if not delivery and order.picked_up_at else status_label(order))
    return {"fulfillment_method": order.fulfillment_method,
        "fulfillment_label": order.get_fulfillment_method_display() if order.fulfillment_method else "Not recorded",
        "fulfillment_progress": progress, "status_label": status_label(order),
        "delivery_destination": order.delivery_destination,
        "delivery_started_at": order.delivery_started_at.isoformat() if order.delivery_started_at else None,
        "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None}


def creation_fields(data):
    """Legacy clients omit method; new clients must provide a valid choice/address."""
    if not isinstance(data, dict): raise ValueError("Send an order object.")
    method = data.get("fulfillment_method", "")
    destination = data.get("delivery_destination", "")
    if not isinstance(method, str) or method not in {"", "pickup", "seller_delivery"}:
        raise ValueError("Select Pickup or Seller Delivery.")
    if not isinstance(destination, str) or len(destination.strip()) > 500:
        raise ValueError("Delivery destination must be text of at most 500 characters.")
    destination = destination.strip()
    if method == "seller_delivery" and not destination:
        raise ValueError("Enter the destination for seller delivery.")
    if method != "seller_delivery" and destination:
        raise ValueError("A delivery destination applies only to Seller Delivery.")
    return {"fulfillment_method": method, "delivery_destination": destination}


@transaction.atomic
def advance(queryset, order_id, action, actor):
    """Authorized adapter supplies scope; lock makes retries/concurrent events safe."""
    order = get_object_or_404(queryset.select_for_update(of=("self",)), pk=order_id)
    if not isinstance(action, str): return JsonResponse({"error": "Select a supported fulfillment action."}, status=400)
    old_status = order.status
    fields = ["updated_at"]
    transitions = {"start_processing": ("pending", "processing"), "ready": ("processing", "ready_for_pickup")}
    notes = ""
    if action in transitions:
        previous, target = transitions[action]
        if order.status == target: return JsonResponse({"order": {"id": order.pk, **presentation(order)}})
        if order.status != previous:
            return JsonResponse({"error": "This order is not eligible for that processing step."}, status=409)
        order.status = target; fields.append("status")
        notes = "Seller processing progress recorded."
    elif action in {"start_delivery", "delivered"}:
        if order.fulfillment_method != "seller_delivery" or order.status != "ready_for_pickup":
            return JsonResponse({"error": "Only a ready Seller Delivery order can record delivery progress."}, status=409)
        field = "delivery_started_at" if action == "start_delivery" else "delivered_at"
        if action == "delivered" and not order.delivery_started_at:
            return JsonResponse({"error": "Record the start of seller delivery before confirming delivery."}, status=409)
        if getattr(order, field): return JsonResponse({"order": {"id": order.pk, **presentation(order)}})
        setattr(order, field, timezone.now()); fields.append(field)
        notes = "Seller delivery started." if action == "start_delivery" else "Seller delivery confirmed; payment and completion remain separate."
    else:
        return JsonResponse({"error": "Select a supported fulfillment action."}, status=400)
    order.save(update_fields=fields)
    MarketplaceOrderStatusHistory.objects.create(order=order, previous_status=old_status,
        new_status=order.status, changed_by=actor, notes=notes)
    return JsonResponse({"message": notes, "order": {"id": order.pk, "status": order.status,
        "payment_status": order.payment_status, **presentation(order)}})
