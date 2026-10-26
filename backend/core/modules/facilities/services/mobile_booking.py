"""Schedule availability and pricing for mobile slot reservations."""

from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from api.models import Booking, Facility
from .operating_schedule import WEEKDAYS, duration_hours, parse_time, parse_time_ranges, weekly_hours
from .rental_configuration import slot_base_amount


def configured_slots(facility, day):
    predefined = parse_time_ranges(facility.slots)
    raw_hours = (facility.workflow_config or {}).get("operating_hours")
    if raw_hours is None or raw_hours == "":
        return predefined
    schedule = weekly_hours(raw_hours)
    if schedule is None:
        # Retain legacy time-only ranges; unknown weekday text fails closed.
        periods = parse_time_ranges(raw_hours, strict=True) if isinstance(raw_hours, str) else []
    else:
        period = schedule[WEEKDAYS[day.weekday()]]
        periods = [(parse_time(period["open"]), parse_time(period["close"]))] if period else []
    if facility.slots:
        return [(start, end) for start, end in predefined
                if any(opening <= start < end <= closing for opening, closing in periods)]
    return periods


def conflicting_bookings(facility, day, start, end, *, room_id=None, exclude_booking=None):
    from .schedules import schedule_blocks_q
    recurring = Q(booking_date__lte=day, mobile_request__details__source="schedule",
        mobile_request__details__schedule__until__gte=day.isoformat()) & (
        Q(mobile_request__details__schedule__repeat="none") |
        Q(mobile_request__details__schedule__repeat="weekly",
          mobile_request__details__schedule__weekdays__contains=[day.weekday()]))
    stays = Q(check_in_date__lte=day, check_out_date__gt=day)
    records = Booking.objects.filter(facility=facility).exclude(
        status__in=(Booking.STATUS_CANCELLED, Booking.STATUS_REJECTED)
    ).filter(Q(booking_date=day, mobile_request__details__schedule__isnull=True) | recurring | stays).filter(
        stays | Q(start_time__lt=end, end_time__gt=start) | Q(start_time__isnull=True) | Q(end_time__isnull=True)
    )
    if room_id:
        records = records.filter(Q(room_id=room_id) | Q(room_id__isnull=True) | schedule_blocks_q())
    if exclude_booking:
        records = records.exclude(pk=exclude_booking)
    return records


def slot_status(facility, day, start, end, *, exclude_booking=None):
    now = timezone.localtime()
    if day < now.date() or (day == now.date() and start <= now.time().replace(tzinfo=None)):
        return "unavailable"
    if facility.availability_status == Facility.STATUS_MAINTENANCE:
        return "maintenance"
    if facility.is_archived or facility.availability_status != Facility.STATUS_AVAILABLE:
        return "unavailable"
    if not facility.slots:
        try:
            minimum = duration_hours((facility.workflow_config or {}).get("minimum_booking_duration"))
        except ValidationError:
            return "unavailable"
        hours = Decimal((datetime.combine(day, end) - datetime.combine(day, start)).seconds) / 3600
        if minimum is not None and hours < minimum:
            return "unavailable"
    if not any(opening <= start < end <= closing for opening, closing in configured_slots(facility, day)):
        return "unavailable"
    conflicts = conflicting_bookings(facility, day, start, end, exclude_booking=exclude_booking)
    for booking in conflicts:
        purpose = (booking.purpose or "").lower()
        if purpose.startswith("[maintenance]"):
            return "maintenance"
        if purpose.startswith("[class]"):
            return "class"
    return "reserved" if conflicts.exists() else "available"


def schedule_payload(facility, day, *, exclude_booking=None):
    return [
        {"start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
         "label": f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}",
         "status": slot_status(facility, day, start, end, exclude_booking=exclude_booking)}
        for start, end in configured_slots(facility, day)
    ]


def conflict_description(booking):
    """Describe an already-found conflict without exposing its client, title or ID."""
    from .schedules import SCHEDULE_TYPES
    purpose = (booking.purpose or "").lstrip().lower()
    kind = next((key for key in SCHEDULE_TYPES if purpose.startswith(f"[{key}]")), None)
    message = f"Conflicts with {SCHEDULE_TYPES[kind]}" if kind else "Overlaps an existing booking"
    if booking.start_time and booking.end_time:
        start = booking.start_time.strftime("%I:%M %p").lstrip("0")
        end = booking.end_time.strftime("%I:%M %p").lstrip("0")
        message += f" · {start}–{end}"
    return message + "."


def rental_quote(facility, day, start, end):
    from .catalog import SERVICE_MODES, SERVICE_TYPES
    if facility.booking_mode != 'slot' or facility.facility_type in SERVICE_TYPES or facility.booking_mode in SERVICE_MODES:
        raise ValidationError("This facility uses a different request process. Contact Facilities Admin.")
    if facility.facility_type in ("food_analysis", "lease_space"):
        raise ValidationError("This facility uses a different request process. Contact Facilities Admin.")
    if (start, end) not in configured_slots(facility, day):
        raise ValidationError("Select one of the configured time slots.")
    if slot_status(facility, day, start, end) != "available":
        raise ValidationError("This time slot is no longer available. Select another schedule.")
    hours = Decimal((datetime.combine(day, end) - datetime.combine(day, start)).seconds) / Decimal(3600)
    if not facility.slots:
        minimum = duration_hours((facility.workflow_config or {}).get("minimum_booking_duration"))
        if minimum is not None and hours < minimum:
            raise ValidationError("This period is shorter than the facility's minimum booking duration.")
    total = slot_base_amount(facility, hours)
    return {"base_amount": str(total), "total_amount": str(total), "hours": str(hours),
            "rate": str(facility.rate), "price_type": facility.price_type,
            "additional_requirements_note": "Additional requirements are subject to availability and a separate quote."}
