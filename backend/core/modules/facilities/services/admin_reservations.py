"""Admin-assisted quotes reuse real rooms, operating periods and core booking rules."""
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from api.models import CampusHubUser, Facility, Room
from .catalog import SERVICE_MODES, SERVICE_TYPES
from .mobile_booking import configured_slots, conflicting_bookings, slot_status, conflict_description
from .operating_schedule import WEEKDAYS, closed_operating_day_messages, parse_time
from .rental_configuration import slot_base_amount, FORM_TYPES, booking_form_for_category


class ReservationUnavailable(ValidationError):
    """A schedule/status/capacity failure, distinguished from pricing or client input."""


def whole_number(value, label, minimum=0):
    try:
        parsed = int(value)
        if isinstance(value, bool) or str(parsed) != str(value) or not minimum <= parsed <= 100000:
            raise ValueError
        return parsed
    except (TypeError, ValueError):
        raise ValidationError(f"Enter a valid whole number for {label}.")


def money(value):
    amount = Decimal(str(value))
    if not amount.is_finite() or amount < 0:
        raise ValidationError("The saved pricing configuration needs review.")
    return amount


def client_details(data, facility=None):
    client_type = data.get("client_type")
    if client_type is not None and client_type not in ("existing", "walkin"):
        raise ValidationError("Select a valid Client Type.")
    if client_type == "existing" and not data.get("client_id"):
        raise ValidationError("Search and select a CampusHub user.")
    if client_type == "walkin" and data.get("client_id"):
        raise ValidationError("Clear the selected account when entering a walk-in client.")
    user = None
    if data.get("client_id"):
        user = CampusHubUser.objects.filter(pk=data["client_id"], is_active=True, is_suspended=False).first()
        if user is None:
            raise ValidationError("Select an active CampusHub client.")
        name = f"{user.first_name} {user.last_name}".strip() or user.username
    else:
        name = str(data.get("full_name") or "").strip()
    if not name or len(name) > 200:
        raise ValidationError("Select a client or enter the walk-in client's full name.")
    contact = str(data.get("contact_number") or (user.contact_number if user else "")).strip()
    email = str(data.get("email") or (user.email if user else "")).strip()
    if not 7 <= len(contact) <= 30:
        raise ValidationError("Enter the client's contact number.")
    if email:
        validate_email(email)
    details = {"source": "admin", "full_name": name, "contact_number": contact, "email": email,
               "organization": str(data.get("organization") or "").strip(),
               "purpose": str(data.get("purpose") or "").strip(),
               "address": str(data.get("address") or "").strip(),
               "notes": str(data.get("notes") or "").strip()}
    if not details["purpose"] or any(len(value) > 2000 for value in details.values()):
        raise ValidationError("Enter a purpose and keep client details below 2,000 characters.")
    if facility and (facility.workflow_config or {}).get("requires_client_address") is True and not details["address"]:
        raise ValidationError("Client address is required by this facility's booking form.")
    return user, details


def reservation_schedule(facility, data, *, check_capacity=True, exclude_booking=None):
    """Validate real schedule fields; optional incomplete client/counts never create a quote."""
    if facility.facility_type in SERVICE_TYPES or facility.booking_mode in SERVICE_MODES:
        raise ReservationUnavailable("Use the service request workflow for this service, not a facility reservation.")
    if facility.availability_status == Facility.STATUS_MAINTENANCE:
        raise ReservationUnavailable("This facility is under maintenance.")
    if facility.is_archived or facility.availability_status != Facility.STATUS_AVAILABLE:
        raise ReservationUnavailable("This facility is not open for booking.")
    workflow = facility.workflow_config or {}
    form = booking_form_for_category(facility.facility_type, workflow)
    guests = whole_number(data.get("attendees"), "participants / guests", 1) if check_capacity else None
    fields = {}
    nights, hours = 0, Decimal("0")
    adults = children = None
    room = None
    if facility.booking_mode == "room":
        first, last = date.fromisoformat(str(data.get("check_in_date", ""))), date.fromisoformat(str(data.get("check_out_date", "")))
        nights = (last - first).days
        if first < timezone.localdate() or not 1 <= nights <= 366:
            raise ReservationUnavailable("Choose future check-in and later check-out dates, within one year.")
        if check_capacity:
            children = whole_number(data.get("children") or 0, "children")
            adults = whole_number(data.get("adults"), "adults", 1) if data.get("adults") not in (None, "") else guests - children
            if adults < 1:
                raise ReservationUnavailable("Enter at least one adult for this stay.")
            if adults + children != guests:
                raise ReservationUnavailable("Adults plus children must equal the number of guests.")
        try:
            room_key = UUID(str(data["room_id"])) if data.get("room_id") else None
        except ValueError:
            raise ReservationUnavailable("Select a valid configured room/unit.")
        room = Room.objects.filter(facility=facility, pk=room_key).first() if room_key else None
        if room is None:
            raise ReservationUnavailable("Select a configured room/unit. Contact Facilities Admin if no rooms exist.")
        if room.status != Room.STATUS_AVAILABLE:
            raise ReservationUnavailable("This room/unit is currently unavailable.")
        if check_capacity and room.capacity and guests > room.capacity:
            raise ReservationUnavailable("The guest count exceeds this room's capacity.")
        for offset in range(nights):
            day = first + timedelta(days=offset)
            conflict = conflicting_bookings(facility, day, time.min, time(23, 59, 59), room_id=room.pk, exclude_booking=exclude_booking).first()
            if conflict:
                raise ReservationUnavailable(conflict_description(conflict))
        fields = {"check_in_date": first, "check_out_date": last, "room_id": room.pk}
        # No fake time fields: configured check-in/out times are retained as display metadata.
    elif facility.booking_mode == "slot":
        day = date.fromisoformat(str(data.get("date", "")))
        start, end = parse_time(data.get("start", "")), parse_time(data.get("end", ""))
        if start >= end:
            raise ReservationUnavailable("End time must be later than start time.")
        closed_message = closed_operating_day_messages(facility).get(WEEKDAYS[day.weekday()])
        if closed_message:
            raise ReservationUnavailable(closed_message)
        if facility.slots and (start, end) not in configured_slots(facility, day):
            raise ReservationUnavailable("Select one of the configured time slots.")
        state = slot_status(facility, day, start, end, exclude_booking=exclude_booking)
        if state != "available":
            if state in ("class", "maintenance", "reserved"):
                conflict = conflicting_bookings(facility, day, start, end, exclude_booking=exclude_booking).first()
                if conflict:
                    raise ReservationUnavailable(conflict_description(conflict))
            messages = {"class": "This time overlaps a Class / Academic Schedule.", "maintenance": "This facility is under maintenance during this time.",
                        "reserved": "This time overlaps an existing booking or facility schedule block."}
            raise ReservationUnavailable(messages.get(state, "This period is outside operating hours, in the past, or shorter than the minimum duration."))
        hours = Decimal((datetime.combine(day, end) - datetime.combine(day, start)).total_seconds()) / 3600
        fields = {"booking_date": day, "start_time": start, "end_time": end}
    else:
        raise ReservationUnavailable("This booking mode needs an approved request process before reservations can be created.")
    if check_capacity and facility.capacity and guests > facility.capacity:
        raise ReservationUnavailable("The participant / guest count exceeds the facility capacity.")
    return fields, {"guests": guests, "adults": adults, "children": children, "nights": nights, "hours": hours, "room": room, "form": form}


def reservation_quote(facility, data, *, exclude_booking=None):
    """Reuse validated schedule plus existing configured pricing; perform no writes."""
    fields, context = reservation_schedule(facility, data, exclude_booking=exclude_booking)
    guests, nights, hours, room, form = (context[key] for key in ("guests", "nights", "hours", "room", "form"))
    workflow = facility.workflow_config or {}
    pricing = workflow.get("pricing", {})
    method = facility.price_type
    shared = data.get("shared_rate") is True
    if method in ("hour", "base_hour", "session"):
        if not hours and method != "session":
            raise ValidationError("Hourly pricing cannot be used for a stay without configured billing times.")
        base = slot_base_amount(facility, hours, include_configured_adjustments=True)
    elif method in ("night", "person_night", "day", "person"):
        if method in ("night", "person_night") and not nights:
            raise ValidationError("This pricing method requires a date-range booking.")
        rate = money(facility.rate)
        if shared:
            if method != "person_night" or not room or not pricing.get("partner_occupancy_required") or guests < int(pricing["partner_occupancy_required"]):
                raise ValidationError("The shared rate requires the configured number of guests in the same room.")
            rate = money(pricing.get("partner_rate"))
        base = rate * ((nights or 1) if method in ("night", "day") else guests * (nights or 1))
    else:
        raise ValidationError("Custom pricing requires an approved quote; an arbitrary total cannot be entered here.")
    if any(item.get("is_active") and item.get("has_additional_fee") for item in workflow.get("equipment", []) if isinstance(item, dict)):
        raise ValidationError("Legacy equipment charges need configuration review before quoting.")
    discount = Decimal("0")
    chosen = data.get("discount_index")
    reason = str(data.get("discount_reason") or "").strip()
    if chosen not in (None, ""):
        if 'verification_method' in data:
            from .booking_workflow import VERIFICATION_METHODS
            method = data.get('verification_method')
            other = str(data.get('verification_other') or '').strip()
            notes = str(data.get('verification_notes') or '').strip()
            if method not in VERIFICATION_METHODS or method == 'Other' and not other or len(other) > 150 or len(notes) > 500:
                raise ValidationError('Select a verification method and specify Other when applicable.')
            reason = (other if method == 'Other' else method) + (': ' + notes if notes else '')
        index = whole_number(chosen, "discount")
        rules = workflow.get("discount_rules", [])
        if index >= len(rules) or not rules[index].get("active") or not reason or len(reason) > (700 if 'verification_method' in data else 500):
            raise ValidationError("Select an active discount and record verified eligibility.")
        rule = rules[index]
        scope = rule["applies_to"]
        basis = base
        if scope == "base_rate":
            basis = money(facility.rate)
        elif scope == "additional_hour_rate":
            basis = max(hours - money(pricing["base_duration"]), Decimal("0")) * money(pricing["additional_hour_rate"])
        elif scope == "individual_rate" and shared or scope == "partner_rate" and not shared:
            raise ValidationError("This discount does not apply to the selected individual/shared rate.")
        elif scope == "custom":
            raise ValidationError("Custom discount scopes need an approved quote.")
        value = money(rule["discount_value"])
        discount = min(basis, basis * value / 100 if rule["discount_type"] == "percentage" else value)
    rental = (base - discount).quantize(Decimal("0.01"))
    charges = []
    quantities = data.get("fee_quantities", {})
    if not isinstance(quantities, dict):
        raise ValidationError("Enter valid additional fee quantities.")
    for index, fee in enumerate(workflow.get("additional_fees", [])):
        if not fee.get("active"):
            continue
        factors = {"hour": hours, "day": nights or 1, "night": nights, "person": guests, "booking": 1, "fixed": 1}
        factor = whole_number(quantities.get(str(index), 0), fee["name"]) if fee["unit"] in ("item", "unit") else factors.get(fee["unit"])
        if factor is None or factor == 0 and fee["unit"] in ("hour", "day", "night"):
            raise ValidationError("The saved additional fee basis needs an approved quote.")
        charges.append({"name": fee["name"], "quantity": str(factor), "amount": str((money(fee["amount"]) * factor).quantize(Decimal("0.01")))})
    fees = sum((Decimal(row["amount"]) for row in charges), Decimal("0"))
    deposit = Decimal("0")
    if workflow.get("damage_deposit_applicable"):
        config = workflow["damage_deposit"]
        value = money(config["value"])
        deposit = value if config["type"] == "fixed" else rental * value / 100
    deposit = deposit.quantize(Decimal("0.01"))
    total = (rental + fees + deposit).quantize(Decimal("0.01"))
    if total > Decimal("99999999.99"):
        raise ValidationError("This total exceeds the supported booking amount.")
    quote = {"base_amount": str(base), "discount_amount": str(discount.quantize(Decimal("0.01"))),
             "rental_amount": str(rental), "fees": charges, "fee_amount": str(fees), "deposit_amount": str(deposit),
             "rental_total": str((rental + fees).quantize(Decimal("0.01"))), "total_amount": str(total), "hours": str(hours), "nights": nights, "form_label": FORM_TYPES[form]}
    quote.update(guests=guests, adults=context["adults"], children=context["children"])
    return fields, quote
