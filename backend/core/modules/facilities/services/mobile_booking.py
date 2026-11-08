"""Schedule availability and pricing for mobile slot reservations."""

from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from api.models import Booking, Facility
from .operating_schedule import WEEKDAYS, duration_hours, parse_time, parse_time_ranges, weekly_hours, booking_day_restriction
from .rental_configuration import slot_base_amount
from .feature_configuration import booking_requirement_options, validate_booking_requirements


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
    records = Booking.objects.filter(facility=facility, status__in=(Booking.STATUS_PENDING, Booking.STATUS_APPROVED)).filter(
        Q(booking_date=day, mobile_request__details__schedule__isnull=True) | recurring | stays).filter(
        stays | Q(mobile_request__details__schedule__all_day=True) |
        Q(start_time__lt=end, end_time__gt=start) | Q(start_time__isnull=True) | Q(end_time__isnull=True)
    )
    if room_id:
        records = records.filter(Q(room_id=room_id) | Q(room_id__isnull=True) | schedule_blocks_q())
    if exclude_booking:
        records = records.exclude(pk=exclude_booking)
    return records


def blocking_kind(booking):
    """Prefer the saved admin type; support legacy prefixed records too."""
    from .schedules import SCHEDULE_TYPES, metadata
    kind = metadata(booking).get("schedule", {}).get("type")
    if kind in SCHEDULE_TYPES:
        return kind
    purpose = (booking.purpose or "").lstrip().lower()
    return next((kind for kind in (*SCHEDULE_TYPES, "blocked", "assessment")
                 if purpose.startswith(f"[{kind}]")), "reservation")


STATUS_REASONS = {
    "available": "An eligible booking period is available.",
    "unavailable": "Outside booking rules, elapsed time, or shorter than the minimum duration.",
    "maintenance": "Maintenance schedule.", "class": "Class / Academic Schedule.",
    "reserved": "An existing reservation occupies this period.",
    "blocked": "Official Campus Use / Administrative Hold or another blocking schedule.",
    "not_bookable": "This date is outside the facility's booking rules.",
}


def date_restriction(facility, day, *, now=None):
    now = now or timezone.localtime()
    if day < now.date():
        return "Past date."
    restriction = booking_day_restriction(facility.workflow_config or {}, day)
    if restriction:
        return restriction
    if not configured_slots(facility, day):
        return "No configured operating periods for this date."
    if facility.is_archived or facility.availability_status not in (Facility.STATUS_AVAILABLE, Facility.STATUS_MAINTENANCE):
        return "This facility is not open for booking."
    return None


def slot_status(facility, day, start, end, *, exclude_booking=None, conflicts=None):
    now = timezone.localtime()
    if day < now.date() or (day == now.date() and start <= now.time().replace(tzinfo=None)):
        return "unavailable"
    if booking_day_restriction(facility.workflow_config or {}, day):
        return "unavailable"
    if not any(opening <= start < end <= closing for opening, closing in configured_slots(facility, day)):
        return "unavailable"
    if facility.availability_status == Facility.STATUS_MAINTENANCE:
        return "maintenance"
    if facility.is_archived or facility.availability_status != Facility.STATUS_AVAILABLE:
        return "unavailable"
    conflicts = list(conflicting_bookings(facility, day, start, end, exclude_booking=exclude_booking).select_related("mobile_request")) if conflicts is None else conflicts
    kinds = {blocking_kind(booking) for booking in conflicts}
    for kind, state in (("maintenance", "maintenance"), ("class", "class"),
                        ("official", "blocked"), ("hold", "blocked"), ("blocked", "blocked"),
                        ("other", "blocked"), ("assessment", "blocked"), ("reservation", "reserved")):
        if kind in kinds:
            return state
    # Preserve the real blocking category even when its interval is shorter
    # than the minimum rental duration; only free intervals can be bookable.
    if not facility.slots:
        try:
            minimum = duration_hours((facility.workflow_config or {}).get("minimum_booking_duration"))
        except ValidationError:
            return "unavailable"
        hours = Decimal((datetime.combine(day, end) - datetime.combine(day, start)).seconds) / 3600
        if minimum is not None and hours < minimum:
            return "unavailable"
    return "available"


def schedule_payload(facility, day, *, exclude_booking=None):
    """Project real operating periods and conflicts, retaining configured presets.

    Without presets, the web accepts custom times inside operating hours. Split
    those hours only at actual conflict/current-time boundaries so a partial
    reservation does not hide the rest of the day's bookable time.
    """
    rows = []
    now = timezone.localtime()
    try:
        minimum = duration_hours((facility.workflow_config or {}).get("minimum_booking_duration"))
        minimum_minutes = int(minimum * 60) if minimum is not None else 0
    except ValidationError:
        minimum_minutes = None  # Invalid saved rules remain unavailable via slot_status.
    for opening, closing in configured_slots(facility, day):
        from .schedules import metadata
        records = list(conflicting_bookings(facility, day, opening, closing,
                       exclude_booking=exclude_booking).select_related("mobile_request"))
        def overlaps(booking, start, end):
            return (metadata(booking).get("schedule", {}).get("all_day") is True or
                    booking.check_in_date is not None or not booking.start_time or not booking.end_time or
                    booking.start_time < end and booking.end_time > start)
        boundaries = {opening, closing}
        if not facility.slots:
            for booking in records:
                if booking.start_time and booking.end_time and not metadata(booking).get("schedule", {}).get("all_day"):
                    boundaries.update(clock for clock in (booking.start_time, booking.end_time)
                                      if opening < clock < closing)
            if day == now.date():
                next_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
                if next_minute.date() == day and opening < next_minute.time().replace(tzinfo=None) < closing:
                    boundaries.add(next_minute.time().replace(tzinfo=None))
        ordered = sorted(boundaries)
        for start, end in zip(ordered, ordered[1:]):
            overlapping = [record for record in records if overlaps(record, start, end)]
            row = {"start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
                   "label": f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}",
                   "status": slot_status(facility, day, start, end, exclude_booking=exclude_booking,
                                         conflicts=overlapping)}
            row["reason"] = STATUS_REASONS[row["status"]]
            if row["status"] not in ("available", "unavailable"):
                from .schedules import SCHEDULE_TYPES
                row["blocking_types"] = sorted({blocking_kind(record) for record in overlapping})
                row["reason"] = " / ".join(SCHEDULE_TYPES.get(kind, "Existing reservation")
                                             for kind in row["blocking_types"]) or row["reason"]
            if not facility.slots:
                row["time_selection"] = "custom"
                row["minimum_duration_minutes"] = minimum_minutes
            rows.append(row)
    return rows


def day_availability(facility, day, *, exclude_booking=None, eligibility_reason=None):
    """Public summary and rows, with restrictions distinct from actual blocks."""
    restriction = eligibility_reason or date_restriction(facility, day)
    rows = schedule_payload(facility, day, exclude_booking=exclude_booking)
    if restriction:
        rows = [{**row, "status": "unavailable", "reason": restriction} for row in rows]
    states = {row["status"] for row in rows}
    status = "not_bookable"
    if not restriction:
        status = next((state for state in ("available", "maintenance", "class", "blocked", "reserved")
                       if state in states), "not_bookable")
    return {"date": day.isoformat(), "status": status, "reason": restriction or STATUS_REASONS[status],
            "slots": rows, "available_slots": [row for row in rows if row["status"] == "available"],
            "blocking_statuses": sorted(states - {"available", "unavailable"})}


def conflict_description(booking):
    """Describe an already-found conflict without exposing its client, title or ID."""
    from .schedules import SCHEDULE_TYPES
    kind = blocking_kind(booking)
    kind = {"blocked": "hold", "assessment": "other"}.get(kind, kind)
    message = f"Conflicts with {SCHEDULE_TYPES[kind]}" if kind in SCHEDULE_TYPES else "Overlaps an existing booking"
    if booking.start_time and booking.end_time:
        start = booking.start_time.strftime("%I:%M %p").lstrip("0")
        end = booking.end_time.strftime("%I:%M %p").lstrip("0")
        message += f" · {start}–{end}"
    return message + "."


def rental_quote(facility, day, start, end, *, data=None, user=None):
    from .catalog import SERVICE_MODES, SERVICE_TYPES
    if facility.booking_mode != 'slot' or facility.facility_type in SERVICE_TYPES or facility.booking_mode in SERVICE_MODES:
        raise ValidationError("This facility uses a different request process. Contact Facilities Admin.")
    if facility.facility_type in ("food_analysis", "lease_space"):
        raise ValidationError("This facility uses a different request process. Contact Facilities Admin.")
    if data is not None and user is not None:
        return complete_mobile_quote(facility, day, start, end, data, user)
    # Import locally: the web validator itself reuses this module's core rules.
    from .admin_reservations import reservation_schedule
    _, context = reservation_schedule(facility, {
        "date": day.isoformat(), "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
    }, check_capacity=False)
    hours = context["hours"]
    total = slot_base_amount(facility, hours)
    return {"base_amount": str(total), "total_amount": str(total), "hours": str(hours),
            "rate": str(facility.rate), "price_type": facility.price_type,
            "additional_requirements_note": "Additional requirements are subject to availability and a separate quote."}


def mobile_pricing_options(facility):
    """Expose saved optional quantities, never seed a rate or deposit."""
    return {"requirement_options": booking_requirement_options(facility), "item_fees": [
        {"index": index, "name": fee["name"], "unit_amount": str(fee["amount"])}
        for index, fee in enumerate((facility.workflow_config or {}).get("additional_fees", []))
        if fee.get("active") and fee.get("unit") in ("item", "unit")]}


def complete_mobile_quote(facility, day, start, end, data, user):
    """Use the staff quote engine, binding discount eligibility to the bearer owner."""
    import json
    from django.core import signing
    from .admin_reservations import reservation_quote, whole_number

    workflow = facility.workflow_config or {}
    quantities = data.get("fee_quantities", {})
    options = {str(fee["index"]): fee for fee in mobile_pricing_options(facility)["item_fees"]}
    if not isinstance(quantities, dict) or any(key not in options for key in quantities):
        raise ValidationError("The optional charges changed. Return to Booking Details and review the quantities.")
    quantities = {key: whole_number(value, options[key]["name"]) for key, value in quantities.items()}
    requirements = validate_booking_requirements(facility, data.get("additional_requirements", []))
    for index, fee in options.items():
        if fee["name"].strip().lower() in ("chair", "chairs", "chair rental") and "Chairs" in requirements and not quantities.get(index):
            raise ValidationError("Enter the number of chairs required.")
    hourly = data.get("use_hourly_rate", False)
    if not isinstance(hourly, bool):
        raise ValidationError("Select a valid rental rate option.")
    details = {"date": day.isoformat(), "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
               "attendees": data.get("attendees"), "client_id": user.pk,
               "fee_quantities": quantities, "use_hourly_rate": hourly}
    # The caller cannot assert a different client, affiliation, or staff evidence.
    _, estimate = reservation_quote(facility, details)
    # Account type, verified email and completed profile are self-service facts,
    # not authoritative institutional-affiliation evidence. The current account
    # schema has no staff-controlled affiliation verification record. Until that
    # dependency exists, use the undiscounted quote; staff can verify a discount
    # per reservation through the existing protected administrative workflow.
    account_type = str(user.user_type or "").strip().lower()
    if data.get("discount_index") not in (None, ""):
        raise ValidationError("This discount requires eligibility verification by Facilities Admin.")
    estimate.update(rate=str(facility.rate), price_type=facility.price_type,
                    pricing_options=mobile_pricing_options(facility))
    # No mobile special-discount application exists; do not imply one is pending.
    estimate["discount_note"] = ""
    priced_names = {row["name"].strip().lower() for row in estimate["fees"]}
    unquoted = [name for name in requirements if name.lower() not in priced_names
                and not (name == "Chairs" and priced_names.intersection({"chair", "chairs", "chair rental"}))]
    estimate["additional_requirements_note"] = (
        "Other selected requirements are subject to availability and a separate admin quote." if unquoted else "")
    signature_data = {"facility": str(facility.pk), "user": user.pk, "request": details,
                      "workflow": workflow, "quote": estimate,
                      "eligibility": {"account_type": account_type,
                                      "affiliation_verification": "unavailable"}}
    estimate["quote_token"] = signing.Signer(salt="campushub.facility-quote").signature(
        json.dumps(signature_data, sort_keys=True, separators=(",", ":"), default=str))
    return estimate
