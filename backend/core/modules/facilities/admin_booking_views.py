"""Protected admin transport for the existing booking and schedule workflow."""
import base64
import json
import uuid
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.activity_logging import log_account_activity
from accounts.models import AccountActivity
from accounts.role_permissions import user_has_admin_access
from api.models import Booking, CampusHubUser, Facility, FacilityBookingRequest
from .services.admin_reservations import client_details, reservation_quote, reservation_schedule, ReservationUnavailable
from .services.catalog import service_resources_q
from .services.mobile_booking import conflicting_bookings
from .services.schedules import (SCHEDULE_TYPES, metadata, schedule_blocks_q,
    schedule_days, validate_schedule, validated_attachment)


def access(request, permission):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Sign in to continue."}, status=401)
    if not user_has_admin_access(request.user) or not request.user.has_perm(f"accounts.{permission}"):
        return JsonResponse({"error": "You do not have access to this action."}, status=403)
    return None


def payload(request):
    data = json.loads(request.body or "{}")
    if not isinstance(data, dict):
        raise ValidationError("Send valid reservation or schedule details.")
    return data


def error_response(error, **details):
    message = error.messages[0] if isinstance(error, ValidationError) else "Check the date, time and request details."
    return JsonResponse({"error": message, **details}, status=400)


def physical_facility(pk, *, lock=False):
    records = Facility.objects.select_for_update() if lock else Facility.objects
    facility = get_object_or_404(records, pk=pk)
    if Facility.objects.filter(pk=pk).filter(service_resources_q()).exists():
        raise ValidationError("Use the service request workflow for this service, not a facility reservation.")
    return facility


def audit(request, booking, action, *, schedule=False):
    inspection = {}
    if action in ('pre_use_inspection_completed', 'post_use_inspection_completed',
                  'pre_use_inspection_updated', 'post_use_inspection_updated',
                  'booking_damage_recorded', 'booking_resolution_completed'):
        kind = 'post' if action.startswith('booking_') else action.split('_', 1)[0]
        record = metadata(booking).get('inspections', {}).get(kind) or {}
        inspection = {'inspection_type': kind, 'inspector_id': (record.get('inspector') or {}).get('id'),
                      'inspector_name': (record.get('inspector') or {}).get('name', ''),
                      'inspected_at': record.get('inspected_at', '')}
    if action == 'booking_personnel_assigned':
        selected = metadata(booking).get('assigned_personnel') or {}
        inspection = {'personnel_id': selected.get('id'), 'personnel_name': selected.get('name', '')}
    log_account_activity(request, source=AccountActivity.SOURCE_ADMIN, account=request.user,
        module="Facilities" if schedule else "Facility Bookings", activity_type=action,
        activity=f"{booking.facility.facility_name if booking.facility else 'Facility'}: {action.replace('_', ' ')}"[:180],
        result=AccountActivity.RESULT_SUCCESS, metadata={"facility_id": str(booking.facility_id),
            "facility_name": booking.facility.facility_name if booking.facility else '', "booking_id": booking.pk, "resource_kind": "physical",
            **({'booking_status': booking.status} if action == 'booking_completed' else {}), **inspection})


@require_GET
def options(request, facility_id):
    denied = access(request, "can_book_facilities")
    if denied is not None:
        return denied
    try:
        facility = physical_facility(facility_id)
        from api.views import serialize_facility
        result = serialize_facility(facility)
        from .services.operating_schedule import closed_operating_day_messages
        result['closed_operating_day_messages'] = closed_operating_day_messages(facility)
        from .services.rental_configuration import booking_form_for_category, FORM_TYPES
        form = booking_form_for_category(facility.facility_type, facility.workflow_config)
        result["booking_form_label"] = FORM_TYPES.get(form, "Booking form needs configuration")
        result["rooms"] = [{"id": str(room.pk), "name": room.room_name or "Room", "capacity": room.capacity,
                            "status": room.status} for room in facility.rooms.all()]
        return JsonResponse({"facility": result})
    except ValidationError as error:
        return error_response(error)


@require_GET
def clients(request):
    denied = access(request, "can_book_facilities")
    if denied is not None:
        return denied
    query = request.GET.get("q", "").strip()[:100]
    rows = []
    if len(query) >= 2:
        name_query = Q()
        for term in query.split():
            name_query &= Q(first_name__icontains=term) | Q(last_name__icontains=term)
        records = CampusHubUser.objects.filter(is_active=True, is_suspended=False).filter(
            name_query | Q(username__icontains=query) |
            Q(student_id__icontains=query) | Q(email__icontains=query)).order_by("first_name", "pk")[:20]
        rows = [{"id": row.pk, "name": f"{row.first_name} {row.last_name}".strip() or row.username,
                 "identifier": row.student_id or row.email, "contact_number": row.contact_number,
                 "email": row.email, "organization": ""} for row in records]
    return JsonResponse({"clients": rows})


@require_POST
def preview(request):
    denied = access(request, "can_book_facilities")
    if denied is not None:
        return denied
    try:
        data = payload(request)
        facility = physical_facility(data.get("facility_id"))
        editing = None
        if data.get('booking_id'):
            from .services.booking_workflow import allowed_actions
            denied = access(request, 'can_manage_bookings')
            if denied is not None:
                return denied
            editing = get_object_or_404(Booking, pk=data['booking_id'], facility=facility)
            if 'edit' not in allowed_actions(editing, request.user):
                raise ValidationError('Only active unpaid bookings can be edited.')
        if data.get("availability_only") is True:
            reservation_schedule(facility, data, check_capacity=False, exclude_booking=editing.pk if editing else None)
            return JsonResponse({"available": True})
        reservation_schedule(facility, data, check_capacity=False, exclude_booking=editing.pk if editing else None)
        try:
            client_details(data, facility)
            fields, quote = reservation_quote(facility, data, exclude_booking=editing.pk if editing else None)
        except ReservationUnavailable:
            raise
        except (ValidationError, ValueError, TypeError, ArithmeticError, KeyError) as error:
            return error_response(error, available=True, stage="pricing")
        return JsonResponse({"available": True, "quote": quote})
    except (ValidationError, ValueError, TypeError, ArithmeticError, KeyError) as error:
        return error_response(error, available=False, stage="availability")


def create(request):
    """Existing /api/bookings/create/ keeps its URL, dispatching by actual purpose."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)
    try:
        data = payload(request)
        kind = data.get("type", "reservation")
        denied = access(request, "can_book_facilities" if kind == "reservation" else "can_manage_schedules")
        if denied is not None:
            return denied
        with transaction.atomic():
            facility = physical_facility(data.get("facility_id"), lock=True)
            if kind != "reservation":
                booking = save_schedule(request, facility, data)
            else:
                user, details = client_details(data, facility)
                fields, quote = reservation_quote(facility, data)
                if str(data.get("quoted_amount", quote["total_amount"])) != quote["total_amount"]:
                    raise ValidationError("The quote changed. Check availability and review the updated amount.")
                details.update({key: data.get(key) for key in ("attendees", "adults", "children", "shared_rate", "discount_index", "discount_reason", "fee_quantities", 'verification_method', 'verification_other', 'verification_notes')})
                details['workflow_snapshot'] = {key:(facility.workflow_config or {}).get(key, False) for key in ('requires_pre_use_inspection','requires_post_use_inspection')}
                for key in ('job_order_stage','check_out_time'):
                    if key in (facility.workflow_config or {}):
                        details['workflow_snapshot'][key] = facility.workflow_config[key]
                details['pricing_method'] = facility.price_type
                may_approve = request.user.has_perm('accounts.can_approve_bookings')
                if may_approve:
                    from .services.booking_workflow import actor
                    details['approval'] = {'by':actor(request.user), 'at':timezone.now().isoformat()}
                details["quote"] = quote
                details["attendees"] = quote["guests"]
                if fields.get("room_id"):
                    details.update(adults=quote["adults"], children=quote["children"])
                details["check_in_time"] = (facility.workflow_config or {}).get("check_in_time", "")
                details["check_out_time"] = (facility.workflow_config or {}).get("check_out_time", "")
                booking = Booking.objects.create(id=f"BK-{timezone.localdate().year}-{uuid.uuid4().hex[:16].upper()}",
                    facility=facility, user=user, **fields, purpose=f"[reservation]\n{details['purpose']}\nReserved by: {details['full_name']}",
                    total_amount=Decimal(quote["total_amount"]), status=Booking.STATUS_APPROVED if may_approve else Booking.STATUS_PENDING)
                from .services.job_order import add_job_order_draft
                add_job_order_draft(booking, details)
                FacilityBookingRequest.objects.create(booking=booking, request_key=uuid.uuid4(), details=details)
                audit(request, booking, "reservation_created")
                if may_approve:
                    audit(request, booking, 'booking_auto_approved')
        from api.views import _serialize_booking_event
        event = _serialize_booking_event(booking)
        if kind == "reservation":
            from .services.booking_workflow import booking_row
            event = booking_row(booking, request.user)
        return JsonResponse({"message": "Facility schedule saved successfully." if kind != "reservation" else "Reservation saved.",
                             "event": event}, status=201)
    except ScheduleConflict as error:
        return JsonResponse({"error": str(error)}, status=409)
    except (ValidationError, ValueError, TypeError, ArithmeticError, KeyError) as error:
        return error_response(error)


class ScheduleConflict(Exception):
    pass


@require_GET
def booking_slip(request, booking_id):
    # Use the same protected official document renderer as the existing API.
    from .booking_workflow_views import document
    return document(request, booking_id, 'slip')


def save_schedule(request, facility, data, booking=None):
    if facility.is_archived:
        raise ValidationError("Reactivate this facility before adding a schedule.")
    first, start, end, config = validate_schedule(data)
    proposed = Booking(facility=facility, booking_date=first, start_time=start, end_time=end)
    # The helper reads the same JSON sidecar used by saved records, without inserting it.
    proposed.mobile_request = FacilityBookingRequest(details={"schedule": config})
    days = list(schedule_days(proposed))
    if not days:
        raise ValidationError("No selected weekdays fall in this date range.")
    for day in days:
        conflicts = conflicting_bookings(facility, day, start, end)
        if booking:
            conflicts = conflicts.exclude(pk=booking.pk)
        if conflicts.exists():
            raise ScheduleConflict("This schedule overlaps an existing booking or facility schedule. Adjust the date or time.")
    old = metadata(booking) if booking else {}
    attachment = validated_attachment(data.get("attachment")) if "attachment" in data else old.get("attachment")
    created = booking is None
    if booking and old.get("schedule") == config and old.get("attachment") == attachment and booking.booking_date == first and booking.start_time == start and booking.end_time == end:
        return booking
    if created:
        booking = Booking(id=f"SC-{uuid.uuid4().hex[:24].upper()}", facility=facility)
    booking.booking_date, booking.start_time, booking.end_time = first, start, end
    booking.purpose = f"[{config['type']}]\n{config['title']}"
    booking.status = Booking.STATUS_APPROVED
    booking.total_amount = 0
    booking.save()
    key = booking.mobile_request.request_key if not created and old else uuid.uuid4()
    FacilityBookingRequest.objects.update_or_create(booking=booking, defaults={"request_key": key,
        "details": {"source": "schedule", "schedule": config, "attachment": attachment}})
    audit(request, booking, "facility_block_added" if created else "facility_block_updated", schedule=True)
    return booking


@require_GET
def schedules(request):
    denied = access(request, "can_manage_schedules")
    if denied is not None:
        return denied
    from api.views import _serialize_booking_event
    rows = Booking.objects.filter(schedule_blocks_q()).exclude(service_resources_q("facility__")).select_related("facility", "mobile_request")
    return JsonResponse({"blocks": [_serialize_booking_event(row) for row in rows.order_by("-created_at")[:300]]})


@require_GET
def calendar(request):
    permission = "can_manage_schedules" if request.user.has_perm("accounts.can_manage_schedules") else "can_view_bookings"
    denied = access(request, permission)
    if denied is not None:
        return denied
    try:
        first = date.fromisoformat(request.GET.get("start", ""))
        last = date.fromisoformat(request.GET.get("end", ""))
        if not 0 <= (last - first).days <= 62:
            raise ValueError
        from .services.calendar import calendar_data, EVENT_TYPES
        event_type = request.GET.get("type", "all")
        if event_type not in {"all", *EVENT_TYPES}:
            raise ValidationError("Select a valid calendar event type.")
        facility_id = request.GET.get("facility", "").strip()
        if facility_id:
            physical_facility(facility_id)
        response = JsonResponse(calendar_data(first, last, facility_id, event_type))
        response["Cache-Control"] = "private, no-store"
        return response
    except (ValueError, ValidationError) as error:
        return error_response(error)


@require_POST
def schedule_update(request, booking_id):
    denied = access(request, "can_manage_schedules")
    if denied is not None:
        return denied
    try:
        data = payload(request)
        # All creation/update/cancellation paths lock the facility first, then its record.
        target = get_object_or_404(Booking.objects.filter(schedule_blocks_q()), pk=booking_id)
        with transaction.atomic():
            facility = physical_facility(target.facility_id, lock=True)
            booking = Booking.objects.select_for_update().get(pk=target.pk)
            if data.get("action") == "cancel":
                if booking.status != Booking.STATUS_CANCELLED:
                    booking.status = Booking.STATUS_CANCELLED
                    booking.save(update_fields=["status", "updated_at"])
                    audit(request, booking, "facility_block_cancelled", schedule=True)
            else:
                if booking.status == Booking.STATUS_CANCELLED:
                    raise ValidationError("Cancelled schedules are kept for history. Add a new schedule instead.")
                if data.get("facility_id") != str(facility.pk):
                    raise ValidationError("A facility schedule cannot be moved to a different facility.")
                booking = save_schedule(request, facility, data, booking)
        from api.views import _serialize_booking_event
        return JsonResponse({"event": _serialize_booking_event(booking)})
    except ScheduleConflict as error:
        return JsonResponse({"error": str(error)}, status=409)
    except (ValidationError, ValueError, TypeError, ArithmeticError, KeyError) as error:
        return error_response(error)


@require_GET
def attachment(request, booking_id):
    # Calendar readers may view supporting evidence; write endpoints stay separate.
    permission = "can_manage_schedules" if request.user.has_perm("accounts.can_manage_schedules") else "can_view_bookings"
    denied = access(request, permission)
    if denied is not None:
        return denied
    booking = get_object_or_404(Booking.objects.filter(schedule_blocks_q()).exclude(service_resources_q("facility__")), pk=booking_id)
    saved = metadata(booking).get("attachment")
    if not saved:
        return JsonResponse({"error": "No attachment is available."}, status=404)
    response = HttpResponse(base64.b64decode(saved["data"]), content_type=saved["type"])
    from django.utils.http import content_disposition_header
    response["Content-Disposition"] = content_disposition_header(True, saved["name"])
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
