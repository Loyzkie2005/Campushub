"""Facility-type rules shared by the admin form and facility API."""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError

from .operating_schedule import WEEKDAYS, duration_hours, validate_weekly_hours, weekly_hours


BOOKING_MODE_LABELS = {
    "slot": "Slot-Based",
    "room": "Room-Based",
    "service": "Service Request",
    "assessment": "Assessment / Schedule-Based",
    "lease": "Lease Application",
}

STATUS_CHOICES = (
    ("available", "Open for Booking"),
    ("unavailable", "Temporarily Unavailable"),
    ("maintenance", "Under Maintenance"),
    ("inactive", "Inactive"),
)

PRICE_TYPE_LABELS = {
    "hour": "Per Hour",
    "session": "Per Session",
    "night": "Per Night",
    "service": "Per Service",
    "monthly": "Monthly",
}

FACILITY_TYPE_CONFIG = {
    "covered_court": {
        "label": "Covered Court",
        "booking_mode": "slot",
        "price_types": ["hour", "session"],
        "default_price_type": "hour",
        "fields": [
            "capacity",
            "rate",
            "operating_hours",
            "minimum_booking_duration",
            "amenities",
        ],
        "required": ["capacity", "rate", "operating_hours"],
    },
    "function_hall": {
        "label": "Function Hall",
        "booking_mode": "slot",
        "price_types": ["hour", "session"],
        "default_price_type": "session",
        "fields": [
            "capacity",
            "rate",
            "operating_hours",
            "minimum_booking_duration",
            "amenities",
        ],
        "required": ["capacity", "rate", "operating_hours"],
    },
    "hostel": {
        "label": "Hostel Accommodation",
        "booking_mode": "room",
        "price_types": ["night"],
        "default_price_type": "night",
        "fields": [
            "rooms_units",
            "room_type",
            "capacity_per_room",
            "rate",
            "check_in_time",
            "check_out_time",
            "amenities",
        ],
        "required": [
            "rooms_units",
            "room_type",
            "capacity_per_room",
            "rate",
            "check_in_time",
            "check_out_time",
        ],
    },
    "food_analysis": {
        "label": "Food Analysis Hub",
        "booking_mode": "service",
        "price_types": ["service"],
        "default_price_type": "service",
        "fields": ["rate", "amenities", "turnaround_information"],
        "required": ["rate", "amenities", "turnaround_information"],
        "amenities_label": "Services Offered",
        "amenities_placeholder": "Type service and press Enter",
        "requirements_label": "Sample Requirements",
    },
    "training_kitchen": {
        "label": "Training Kitchen / Assessment Center",
        "booking_mode": "assessment",
        "price_types": ["hour", "session"],
        "default_price_type": "session",
        "fields": ["capacity", "rate", "assessment_service_type", "amenities"],
        "required": ["capacity", "rate", "assessment_service_type"],
        "amenities_label": "Amenities / Equipment",
    },
    "lease_space": {
        "label": "Lease of Space",
        "booking_mode": "lease",
        "price_types": ["monthly"],
        "default_price_type": "monthly",
        "fields": ["rooms_units", "area_size", "rate"],
        "required": ["rooms_units", "area_size", "rate"],
        "units_label": "Number of Units / Spaces",
        "requirements_label": "Lease Requirements",
        "rate_label": "Monthly Rate",
    },
    # Existing records may still use Other. It is retained for compatibility,
    # but the Add Facility UI does not offer it for new records.
    "other": {
        "label": "Other",
        "booking_mode": "slot",
        "price_types": ["hour", "session"],
        "default_price_type": "hour",
        "fields": ["capacity", "rate", "operating_hours", "amenities"],
        "required": ["rate"],
    },
}

WORKFLOW_CONFIG_FIELDS = {
    "operating_hours",
    "minimum_booking_duration",
    "capacity_per_room",
    "check_in_time",
    "check_out_time",
    "turnaround_information",
    "assessment_service_type",
    "area_size",
}


def facility_form_configuration():
    """Return JSON-safe form rules for the admin template."""
    return {
        "types": FACILITY_TYPE_CONFIG,
        "booking_mode_labels": BOOKING_MODE_LABELS,
        "price_type_labels": PRICE_TYPE_LABELS,
        "weekdays": list(WEEKDAYS),
        "amenities": ["Basketball Court", "Bleachers", "Restrooms", "Parking Area", "Lighting",
                      "Sound System", "Projector", "Air Conditioning"],
        "services": ["Protein Analysis", "Carbohydrate Analysis", "Fat Analysis", "Fiber Analysis",
                     "Moisture Analysis", "Calorie Analysis", "pH Analysis", "Total Solids", "Insoluble Solids"],
    }


def normalize_facility_status(value):
    """Map legacy facility states to the current facility-level statuses."""
    status = str(value or "available").strip().lower()
    if status in {"reserved", "occupied"}:
        return "unavailable"
    return status


def _positive_integer(value, field_name, errors, *, required=False):
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        errors[field_name] = "Enter a valid whole number."
        return 0
    if parsed < 0 or (required and parsed < 1):
        errors[field_name] = "Enter a value greater than zero."
    return max(parsed, 0)


def _nonnegative_decimal(value, errors, *, required=False):
    try:
        parsed = Decimal(str(value or "0"))
    except (InvalidOperation, TypeError, ValueError):
        errors["rate"] = "Enter a valid rate."
        return Decimal("0")
    if parsed < 0 or (required and parsed <= 0):
        errors["rate"] = "Enter a rate greater than zero."
    return max(parsed, Decimal("0"))


def validate_facility_payload(data, *, facility=None):
    """Normalize an Add/Edit payload and enforce type-specific combinations."""
    errors = {}
    facility_type = str(data.get("facility_type") or "").strip().lower()
    config = FACILITY_TYPE_CONFIG.get(facility_type)
    if config is None:
        errors["facility_type"] = "Select a valid facility type."
        config = FACILITY_TYPE_CONFIG["other"]

    name = str(data.get("name") or "").strip()
    location = str(data.get("location") or "").strip()
    if not name:
        errors["name"] = "Facility name is required."
    if not location:
        errors["location"] = "Location is required."

    expected_mode = config["booking_mode"]
    booking_mode = str(data.get("mode") or expected_mode).strip().lower()
    if booking_mode != expected_mode:
        errors["mode"] = (
            f"{config['label']} must use {BOOKING_MODE_LABELS[expected_mode]}."
        )

    status = normalize_facility_status(data.get("status"))
    valid_statuses = {choice[0] for choice in STATUS_CHOICES}
    if status not in valid_statuses:
        errors["status"] = "Select a valid facility status."

    price_type = str(
        data.get("price_type") or config["default_price_type"]
    ).strip().lower()
    if price_type not in config["price_types"]:
        allowed = ", ".join(PRICE_TYPE_LABELS[item] for item in config["price_types"])
        errors["price_type"] = f"{config['label']} supports only: {allowed}."

    required_fields = set(config.get("required", []))
    visible_fields = set(config.get("fields", []))
    capacity = _positive_integer(
        data.get("capacity"), "capacity", errors, required="capacity" in required_fields
    )
    rooms_units = _positive_integer(
        data.get("rooms_units"),
        "rooms_units",
        errors,
        required="rooms_units" in required_fields,
    )
    rate = _nonnegative_decimal(data.get("rate"), errors, required="rate" in required_fields)

    room_type = str(data.get("room_type") or "").strip()
    if "room_type" in required_fields and not room_type:
        errors["room_type"] = "Room type is required for hostel facilities."

    amenities = data.get("amenities") or []
    if not isinstance(amenities, list):
        errors["amenities"] = "Amenities or services must be a list."
        amenities = []
    if any(not isinstance(item, str) or len(item.strip()) > 200 for item in amenities):
        errors["amenities"] = "Each amenity or service must be text of at most 200 characters."
        amenities = []
    amenities = list(dict.fromkeys(item.strip() for item in amenities if item.strip()))
    if "amenities" in required_fields and not amenities:
        errors["amenities"] = "Add at least one service offered."

    raw_workflow = data.get("workflow_config") or {}
    if not isinstance(raw_workflow, dict):
        errors["workflow_config"] = "Facility workflow details are invalid."
        raw_workflow = {}
    workflow_config = {
        key: str(raw_workflow.get(key) or "").strip()
        for key in WORKFLOW_CONFIG_FIELDS
        if key in visible_fields and key not in {"operating_hours", "minimum_booking_duration"}
        and str(raw_workflow.get(key) or "").strip()
    }
    if "operating_hours" in visible_fields:
        hours = raw_workflow.get("operating_hours")
        if isinstance(hours, dict):
            try:
                workflow_config["operating_hours"] = validate_weekly_hours(hours)
                if "operating_hours" in required_fields and not any(hours.values()):
                    errors["operating_hours"] = "Select at least one operating day."
            except ValidationError as error:
                errors["operating_hours"] = error.messages[0]
        elif isinstance(hours, str) and hours.strip():
            # Older clients may still send text. Normalize only when unambiguous.
            workflow_config["operating_hours"] = weekly_hours(hours) or hours.strip()
        elif hours not in (None, ""):
            errors["operating_hours"] = "Operating schedule must contain the seven weekdays."
    has_predefined_slots = bool(facility and facility.slots)
    if "minimum_booking_duration" in visible_fields and not has_predefined_slots:
        try:
            duration = duration_hours(raw_workflow.get("minimum_booking_duration"))
            if duration is not None:
                workflow_config["minimum_booking_duration"] = str(duration)
        except ValidationError as error:
            errors["minimum_booking_duration"] = error.messages[0]
    for field_name in required_fields & WORKFLOW_CONFIG_FIELDS:
        if not workflow_config.get(field_name) and field_name not in errors:
            label = field_name.replace("_", " ").capitalize()
            errors[field_name] = f"{label} is required for {config['label']}."

    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "facility_type": facility_type,
        "location": location,
        "description": str(data.get("description") or "").strip(),
        "capacity": capacity if "capacity" in visible_fields else 0,
        "rate": rate,
        "price_type": price_type,
        "booking_mode": expected_mode,
        "rooms_units": rooms_units if "rooms_units" in visible_fields else None,
        "room_type": room_type if "room_type" in visible_fields else None,
        "amenities": amenities if "amenities" in visible_fields else [],
        "availability_status": status,
        "requirements": str(data.get("requirements") or "").strip(),
        "terms_conditions": str(data.get("terms_conditions") or "").strip(),
        "workflow_config": workflow_config,
    }
