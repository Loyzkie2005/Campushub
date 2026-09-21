"""Authenticated mobile facility booking endpoints."""

import json
import uuid
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from accounts.models import User
from api.models import Booking, Facility, FacilityBookingRequest
from api.views import _mobile_user_from_bearer, serialize_facility
from .services.mobile_booking import parse_time, rental_quote, schedule_payload


def _payload(request):
    data = json.loads(request.body or "{}")
    if not isinstance(data, dict):
        raise ValueError("Invalid request body.")
    return data


def _schedule(data):
    return date.fromisoformat(str(data.get("date", ""))), parse_time(str(data.get("start", ""))), parse_time(str(data.get("end", "")))


def _error(error):
    message = error.messages[0] if isinstance(error, ValidationError) else "Check the date, time, and request details."
    return JsonResponse({"error": message}, status=400)


def _serialize(booking):
    try:
        details = booking.mobile_request.details
    except FacilityBookingRequest.DoesNotExist:
        details = {}
    payments = list(booking.payments.filter(payment_status="paid"))
    paid = sum((payment.paid_amount for payment in payments), Decimal("0"))
    is_paid = bool(payments) and paid >= booking.total_amount
    return {
        "id": booking.pk, "status": booking.status,
        "facility": serialize_facility(booking.facility) if booking.facility else None,
        "date": booking.booking_date.isoformat() if booking.booking_date else "",
        "start": booking.start_time.strftime("%H:%M") if booking.start_time else "",
        "end": booking.end_time.strftime("%H:%M") if booking.end_time else "",
        "created_at": booking.created_at.isoformat(),
        "total_amount": str(booking.total_amount), "paid_amount": str(paid),
        "payment_status": "paid" if is_paid else "unpaid", "details": details,
        "can_cancel": booking.status == Booking.STATUS_PENDING,
        "can_view_slip": booking.status in (Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
        "receipts": [{"number": p.official_receipt_no or "", "amount": str(p.paid_amount),
                      "paid_at": p.paid_at.isoformat() if p.paid_at else None} for p in payments],
    }


@require_GET
def availability(request, facility_id):
    facility = get_object_or_404(Facility, pk=facility_id, is_archived=False)
    try:
        day = date.fromisoformat(request.GET.get("date", ""))
    except ValueError as error:
        return _error(error)
    return JsonResponse({"date": day.isoformat(), "slots": schedule_payload(facility, day)})


@require_GET
def contact(request):
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    admin = User.objects.filter(is_active=True, role="Facilities Admin").order_by("pk").first()
    if admin is None:
        admin = User.objects.filter(is_active=True, role="Super Admin").order_by("pk").first()
    if admin is None:
        return JsonResponse({"error": "No Facilities Admin is available for messaging."}, status=404)
    return JsonResponse({"actor_key": f"admin:{admin.pk}", "name": admin.get_full_name() or admin.username})


@csrf_exempt
@require_POST
def quote(request, facility_id):
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    facility = get_object_or_404(Facility, pk=facility_id, is_archived=False)
    try:
        return JsonResponse(rental_quote(facility, *_schedule(_payload(request))))
    except (ValueError, ValidationError, ArithmeticError) as error:
        return _error(error)


def _details(data, user):
    fields = {key: str(data.get(key, "")).strip() for key in (
        "full_name", "organization", "contact_number", "email", "event_name", "purpose", "notes", "other_requirements",
    )}
    for key in ("full_name", "contact_number", "email", "event_name", "purpose"):
        if not fields[key]:
            raise ValidationError(f"{key.replace('_', ' ').title()} is required.")
    if any(len(value) > 2000 for value in fields.values()):
        raise ValidationError("Keep each field below 2,000 characters.")
    validate_email(fields["email"])
    if not 7 <= len(fields["contact_number"]) <= 30:
        raise ValidationError("Enter a valid contact number.")
    fields["attendees"] = int(data.get("attendees", 0))
    if fields["attendees"] < 1:
        raise ValidationError("Enter at least one attendee.")
    requirements = data.get("additional_requirements", [])
    allowed = {"Chairs", "Tables", "Sound System", "Projector", "Others"}
    if not isinstance(requirements, list) or any(not isinstance(item, str) or item not in allowed for item in requirements):
        raise ValidationError("Select valid additional requirements.")
    if "Others" in requirements and not fields["other_requirements"]:
        raise ValidationError("Specify your other requirements.")
    fields["additional_requirements"] = list(dict.fromkeys(requirements))
    return fields


@csrf_exempt
def bookings(request):
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    if request.method == "GET":
        records = Booking.objects.filter(user=user).select_related("facility", "mobile_request").prefetch_related("payments")
        return JsonResponse({"bookings": [_serialize(row) for row in records[:100]]})
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)
    try:
        data = _payload(request)
        request_key = uuid.UUID(str(data.get("request_key", "")))
        day, start, end = _schedule(data)
        details = _details(data, user)
        with transaction.atomic():
            # Serialize creation per facility, including retries after a lost response.
            facility = get_object_or_404(Facility.objects.select_for_update(), pk=data.get("facility_id"), is_archived=False)
            previous = FacilityBookingRequest.objects.filter(request_key=request_key).select_related("booking").first()
            if previous:
                if previous.booking.user_id != user.pk or previous.booking.facility_id != facility.pk:
                    return JsonResponse({"error": "Request key already used."}, status=409)
                return JsonResponse({"booking": _serialize(previous.booking)})
            estimate = rental_quote(facility, day, start, end)
            if "quoted_amount" in data and Decimal(str(data["quoted_amount"])) != Decimal(estimate["total_amount"]):
                raise ValidationError("The rental rate has changed. Go back and review the updated estimate.")
            if facility.capacity and details["attendees"] > facility.capacity:
                raise ValidationError("The attendee count exceeds the facility capacity.")
            details["quote"] = estimate
            summary = ["[reservation]", details["event_name"], details["purpose"],
                       f"Reserved by: {details['full_name']}",
                       f"Organization: {details['organization']}",
                       f"Contact: {details['contact_number']}", f"Email: {details['email']}",
                       f"Attendees: {details['attendees']}",
                       "Requirements: " + ", ".join(details["additional_requirements"]),
                       details["other_requirements"], details["notes"]]
            booking = Booking.objects.create(
                id=f"BK-{timezone.localdate().year}-{uuid.uuid4().hex[:16].upper()}",
                user=user, facility=facility, booking_date=day, start_time=start, end_time=end,
                purpose="\n".join(filter(None, summary)), total_amount=Decimal(estimate["total_amount"]),
                status=Booking.STATUS_PENDING,
            )
            FacilityBookingRequest.objects.create(booking=booking, request_key=request_key, details=details)
        return JsonResponse({"booking": _serialize(booking)}, status=201)
    except (ValueError, TypeError, ValidationError, ArithmeticError) as error:
        return _error(error)


@require_GET
def booking_detail(request, booking_id):
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    booking = get_object_or_404(Booking, pk=booking_id, user=user)
    return JsonResponse({"booking": _serialize(booking)})


@csrf_exempt
@require_POST
def cancel(request, booking_id):
    user, error = _mobile_user_from_bearer(request)
    if error is not None:
        return error
    with transaction.atomic():
        booking = get_object_or_404(Booking.objects.select_for_update(), pk=booking_id, user=user)
        if booking.status != Booking.STATUS_PENDING:
            return JsonResponse({"error": "Only pending requests can be cancelled. Contact Facilities Admin."}, status=409)
        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=["status", "updated_at"])
    return JsonResponse({"booking": _serialize(booking)})
