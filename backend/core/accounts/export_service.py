"""Role-scoped structured data exports for CampusHub administrators."""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from django.utils import timezone

from api.models import (
    Booking,
    Facility,
    FacilityPayment,
    MarketplaceOrderStatusHistory,
    Product,
    Room,
    SellerRequest,
)
from modules.marketplace.services.inventory import (
    count_customization_options,
    get_product_inventory_status,
    get_product_total_stock,
)
from modules.marketplace.services.order_access import admin_order_queryset
from modules.marketplace.services.product_access import admin_product_queryset


EXPORT_FORMAT = "ZIP archive containing JSON and CSV files"
SCHEDULE_TYPE_PATTERN = re.compile(
    r"^\[(class|reservation|maintenance|assessment)\]\s*", re.IGNORECASE
)


def _serializable(value):
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.isoformat()
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable(item) for item in value]
    return value


def _csv_value(value):
    value = _serializable(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if value is None:
        return ""
    return value


def _write_dataset(archive, name, rows):
    safe_rows = [_serializable(row) for row in rows]
    archive.writestr(
        f"{name}.json",
        json.dumps(safe_rows, ensure_ascii=False, indent=2),
    )

    output = io.StringIO(newline="")
    if safe_rows:
        columns = list(safe_rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in safe_rows:
            writer.writerow({column: _csv_value(row.get(column)) for column in columns})
    archive.writestr(f"{name}.csv", output.getvalue())


def _apply_created_range(queryset, start_date=None, end_date=None):
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    return queryset


def _display_name(user):
    if user is None:
        return ""
    full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
    return full_name or getattr(user, "username", "") or ""


def _department_name(user):
    department = getattr(user, "department", None)
    return getattr(department, "name", "") if department else ""


def _variant_rows(product):
    rows = []
    for group_index, group in enumerate(product.customization_options or [], start=1):
        if not isinstance(group, dict):
            continue
        for option_index, option in enumerate(group.get("options") or [], start=1):
            if not isinstance(option, dict):
                continue
            rows.append({
                "product_id": product.id,
                "product_code": product.product_code or "",
                "group_index": group_index,
                "group_name": group.get("name", ""),
                "selection_type": group.get("selection", "single"),
                "required": bool(group.get("required", False)),
                "option_index": option_index,
                "option_name": option.get("name", ""),
                "extra_price": option.get("extra_price", "0.00"),
                "stock": option.get("stock", ""),
                "expiry_date": option.get("expiry_date", ""),
                "active": option.get("active", True),
            })
    return rows


def _order_item_rows(order):
    items = (order.customization or {}).get("items")
    if not isinstance(items, list) or not items:
        items = [{
            "product_id": order.product_id,
            "product_name": order.product_name,
            "category": order.category,
            "option": order.option,
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "subtotal": order.total_price,
            "customization": order.customization or {},
        }]

    rows = []
    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        rows.append({
            "order_id": order.id,
            "order_code": order.order_code or "",
            "line_number": position,
            "product_id": item.get("product_id") or order.product_id,
            "product_name": item.get("product_name") or order.product_name,
            "category": item.get("category") or order.category,
            "option": item.get("option") or item.get("variant") or "",
            "quantity": item.get("quantity", 1),
            "unit_price": item.get("unit_price", order.unit_price),
            "subtotal": item.get("subtotal", item.get("total_price", order.total_price)),
            "customization": item.get("customization", {}),
        })
    return rows


def _marketplace_datasets(user, start_date=None, end_date=None):
    products = list(
        admin_product_queryset(user)
        .select_related("seller__department", "approved_by", "created_by")
        .order_by("id")
    )
    orders_queryset = _apply_created_range(
        admin_order_queryset(user).select_related("product"),
        start_date,
        end_date,
    )
    orders = list(orders_queryset.order_by("id"))
    order_ids = [order.id for order in orders]
    histories = list(
        MarketplaceOrderStatusHistory.objects.filter(order_id__in=order_ids)
        .order_by("order_id", "created_at", "id")
    )
    seller_requests = list(
        _apply_created_range(
            SellerRequest.objects.select_related("user__department", "reviewed_by"),
            start_date,
            end_date,
        ).order_by("id")
    )

    seller_users = {}
    for product in products:
        seller_users[product.seller_id] = product.seller
    for seller_request in seller_requests:
        if seller_request.user_id:
            seller_users[seller_request.user_id] = seller_request.user

    product_rows = [{
        "id": product.id,
        "product_code": product.product_code or "",
        "seller_id": product.seller_id,
        "seller_name": _display_name(product.seller),
        "seller_department": _department_name(product.seller),
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "base_price": product.price,
        "stock": product.stock,
        "expiry_date": product.expiry_date,
        "customization_enabled": product.customization_enabled,
        "customization_options": product.customization_options or [],
        "approval_status": product.approval_status,
        "is_archived": product.is_archived,
        "rejection_reason": product.rejection_reason,
        "submitted_at": product.submitted_at,
        "updated_at": product.updated_at,
        "approved_at": product.approved_at,
        "approved_by_id": product.approved_by_id,
        "created_by_id": product.created_by_id,
        "image_urls": product.get_image_list(),
    } for product in products]

    variant_rows = [row for product in products for row in _variant_rows(product)]
    inventory_rows = [{
        "product_id": product.id,
        "product_code": product.product_code or "",
        "product_name": product.name,
        "stored_product_stock": product.stock,
        "calculated_total_stock": get_product_total_stock(product),
        "variant_count": count_customization_options(product.customization_options),
        "inventory_status": get_product_inventory_status(product),
        "expiry_date": product.expiry_date,
        "updated_at": product.updated_at,
    } for product in products]

    seller_rows = [{
        "user_id": seller.id,
        "username": seller.username,
        "full_name": _display_name(seller),
        "email": seller.email,
        "contact_number": seller.contact_number,
        "department": _department_name(seller),
        "account_active": seller.is_active,
        "account_suspended": seller.is_suspended,
    } for _seller_id, seller in sorted(seller_users.items())]

    seller_request_rows = [{
        "id": request.id,
        "user_id": request.user_id,
        "student_id": request.student_id,
        "full_name": request.full_name,
        "course_section": request.course_section,
        "contact_number": request.contact_number,
        "product_type": request.product_type,
        "message": request.message,
        "status": request.status,
        "reviewed_by_id": request.reviewed_by_id,
        "reviewed_at": request.reviewed_at,
        "rejection_reason": request.rejection_reason,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
    } for request in seller_requests]

    order_rows = [{
        "id": order.id,
        "order_code": order.order_code or "",
        "product_id": order.product_id,
        "buyer_user_id": order.buyer_user_id,
        "buyer_name": order.buyer_name,
        "buyer_email": order.buyer_email,
        "product_name": order.product_name,
        "category": order.category,
        "seller_name": order.seller_name,
        "seller_contact": order.seller_contact,
        "message_to_seller": order.message_to_seller,
        "option": order.option,
        "customization": order.customization or {},
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "total_price": order.total_price,
        "status": order.status,
        "payment_status": order.payment_status,
        "official_receipt_no": order.official_receipt_no,
        "payment_encoded_by": order.payment_encoded_by,
        "paid_at": order.paid_at,
        "pickup_location": order.pickup_location,
        "pickup_scheduled_at": order.pickup_scheduled_at,
        "picked_up_at": order.picked_up_at,
        "cancellation_reason": order.cancellation_reason,
        "cancelled_at": order.cancelled_at,
        "completed_at": order.completed_at,
        "inventory_deducted": order.inventory_deducted,
        "inventory_restored": order.inventory_restored,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    } for order in orders]
    order_item_rows = [row for order in orders for row in _order_item_rows(order)]

    history_rows = [{
        "id": history.id,
        "order_id": history.order_id,
        "previous_status": history.previous_status,
        "new_status": history.new_status,
        "changed_by": history.changed_by,
        "notes": history.notes,
        "created_at": history.created_at,
    } for history in histories]

    return {
        "products": product_rows,
        "product_variants": variant_rows,
        "inventory": inventory_rows,
        "sellers": seller_rows,
        "seller_requests": seller_request_rows,
        "orders": order_rows,
        "order_items": order_item_rows,
        "order_status_history": history_rows,
    }


def _schedule_details(booking):
    purpose = (booking.purpose or "").strip()
    match = SCHEDULE_TYPE_PATTERN.match(purpose)
    schedule_type = match.group(1).lower() if match else "reservation"
    if match:
        purpose = purpose[match.end():].strip()
    return schedule_type, purpose


def _facility_datasets(start_date=None, end_date=None):
    facilities = list(Facility.objects.all().order_by("id"))
    rooms = list(Room.objects.select_related("facility").all().order_by("facility_id", "id"))
    bookings = list(
        _apply_created_range(
            Booking.objects.select_related("facility", "user__department"),
            start_date,
            end_date,
        ).order_by("id")
    )
    booking_ids = [booking.id for booking in bookings]
    payments = list(
        FacilityPayment.objects.filter(booking_id__in=booking_ids)
        .select_related("booking")
        .order_by("id")
    )

    facility_rows = [{
        "id": facility.id,
        "facility_name": facility.facility_name,
        "facility_type": facility.facility_type,
        "location": facility.location,
        "description": facility.description,
        "capacity": facility.capacity,
        "rate": facility.rate,
        "price_type": facility.price_type,
        "booking_mode": facility.booking_mode,
        "rooms_units": facility.rooms_units,
        "room_type": facility.room_type,
        "amenities": facility.amenities or [],
        "slot_details": facility.slots,
        "requirements": facility.requirements,
        "terms_conditions": facility.terms_conditions,
        "workflow_config": facility.workflow_config or {},
        "image_url": facility.image_url,
        "availability_status": facility.availability_status,
        "created_by_id": facility.created_by_id,
        "created_at": facility.created_at,
        "updated_at": facility.updated_at,
    } for facility in facilities]

    room_rows = [{
        "id": room.id,
        "facility_id": room.facility_id,
        "room_name": room.room_name,
        "room_type": room.room_type,
        "description": room.descriptions,
        "capacity": room.capacity,
        "price": room.price,
        "status": room.status,
        "created_at": room.created_at,
        "updated_at": room.updated_at,
    } for room in rooms]

    booking_rows = []
    schedule_rows = []
    for booking in bookings:
        schedule_type, public_purpose = _schedule_details(booking)
        requester = booking.user
        booking_rows.append({
            "id": booking.id,
            "user_id": booking.user_id,
            "requester_name": _display_name(requester),
            "requester_username": getattr(requester, "username", "") if requester else "",
            "requester_email": getattr(requester, "email", "") if requester else "",
            "requester_contact": getattr(requester, "contact_number", "") if requester else "",
            "requester_department": _department_name(requester),
            "facility_id": booking.facility_id,
            "room_id": booking.room_id,
            "purpose": public_purpose,
            "schedule_type": schedule_type,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "check_in_date": booking.check_in_date,
            "check_out_date": booking.check_out_date,
            "total_amount": booking.total_amount,
            "status": booking.status,
            "created_at": booking.created_at,
            "updated_at": booking.updated_at,
        })
        schedule_rows.append({
            "booking_id": booking.id,
            "facility_id": booking.facility_id,
            "room_id": booking.room_id,
            "schedule_type": schedule_type,
            "date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "check_in_date": booking.check_in_date,
            "check_out_date": booking.check_out_date,
            "purpose": public_purpose,
            "status": booking.status,
        })

    payment_rows = [{
        "id": payment.id,
        "booking_id": payment.booking_id,
        "paid_amount": payment.paid_amount,
        "payment_status": payment.payment_status,
        "official_receipt_no": payment.official_receipt_no,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
    } for payment in payments]

    return {
        "facilities": facility_rows,
        "rooms": room_rows,
        "bookings": booking_rows,
        "schedules": schedule_rows,
        "facility_payments": payment_rows,
    }


def export_record_counts(scope, user=None):
    if scope == "marketplace":
        return {
            "Products": admin_product_queryset(user).count(),
            "Seller requests": SellerRequest.objects.count(),
            "Orders": admin_order_queryset(user).count(),
            "Status history": MarketplaceOrderStatusHistory.objects.filter(
                order__in=admin_order_queryset(user)
            ).count(),
        }
    if scope == "facilities":
        return {
            "Facilities": Facility.objects.count(),
            "Rooms / units": Room.objects.count(),
            "Bookings / schedules": Booking.objects.count(),
            "Payments / receipts": FacilityPayment.objects.count(),
        }
    raise ValueError("Unsupported export scope.")


def build_scoped_export(scope, *, user=None, start_date=None, end_date=None):
    if scope == "marketplace":
        datasets = _marketplace_datasets(user, start_date, end_date)
    elif scope == "facilities":
        datasets = _facility_datasets(start_date, end_date)
    else:
        raise ValueError("Unsupported export scope.")

    generated_at = timezone.localtime()
    manifest = {
        "product": "CampusHub",
        "export_scope": scope,
        "generated_at": generated_at,
        "generated_by": getattr(user, "username", "") or "",
        "generated_by_role": getattr(user, "role", "") or "",
        "format": EXPORT_FORMAT,
        "record_counts": {name: len(rows) for name, rows in datasets.items()},
        "date_range": {
            "from": start_date,
            "to": end_date,
            "note": (
                "The optional range filters transactional records. Current catalog "
                "and facility configuration snapshots remain included."
            ),
        },
        "restorable": False,
        "notice": "This scoped data export is for archival/reference use and is not a system backup.",
    }

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(_serializable(manifest), ensure_ascii=False, indent=2),
        )
        for name, rows in datasets.items():
            _write_dataset(archive, name, rows)

    filename = f"campushub_{scope}_{generated_at.strftime('%Y-%m-%d_%H%M')}.zip"
    return filename, output.getvalue()
