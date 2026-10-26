"""Facility-type rules shared by the admin form and facility API."""

from decimal import Decimal
import unicodedata

from django.core.exceptions import ValidationError

from .operating_schedule import WEEKDAYS, duration_hours, validate_weekly_hours, weekly_hours, parse_time
from .rental_configuration import DISCOUNT_CLIENTS, DISCOUNT_TYPES, DISCOUNT_SCOPES, DISCOUNT_SCOPE_METHODS, FORM_DEFAULTS, FORM_TYPES, FEE_UNITS, PRICING_METHODS, RULE_FIELDS, number, validate_rental_options
from .feature_configuration import FEATURES, validate_features


BOOKING_MODE_LABELS = {
    "slot": "Slot-Based",
    "room": "Room / Stay-Based",
    "daily": "Daily",
    "custom": "Custom",
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
        "label": "Court / Sports Facility",
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
        "label": "Hall / Function Space",
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
        "label": "Hostel / Room Accommodation",
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
    # Other supports future physical rental resources through the same form.
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
        "price_type_labels": {**PRICE_TYPE_LABELS, **PRICING_METHODS},
        "pricing_methods": PRICING_METHODS,
        "booking_form_types": FORM_TYPES,
        "booking_form_defaults": FORM_DEFAULTS,
        "fee_units": FEE_UNITS,
        "discount_clients": DISCOUNT_CLIENTS,
        "discount_types": DISCOUNT_TYPES,
        "discount_scopes": DISCOUNT_SCOPES,
        "discount_scopes_by_method": {method: {scope: DISCOUNT_SCOPES[scope] for scope in scopes} for method, scopes in DISCOUNT_SCOPE_METHODS.items()},
        "weekdays": list(WEEKDAYS),
        "amenities": FEATURES,
        "service_amenities": ["Bleachers", "Restrooms", "Parking Area", "Lighting", "Sound System", "Projector", "Air Conditioning", "Chairs", "Tables", "Bedding", "Fans", "Stage"],
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
    parsed = number(value, field_name, errors, required=required, integer=True, maximum=Decimal("2147483647"))
    if required and parsed == 0:
        errors[field_name] = "Enter a value greater than zero."
    return parsed or 0


def _nonnegative_decimal(value, errors, *, required=False):
    parsed = number(value, "rate", errors, required=required)
    return parsed


def validate_facility_payload(data, *, facility=None):
    """Normalize an Add/Edit payload and enforce type-specific combinations."""
    if not isinstance(data, dict):
        raise ValidationError({"configuration": "Facility configuration must be an object."})
    saved_service = (facility.workflow_config or {}).get("service") if facility else None
    if data.get("catalog_kind") == "service" or isinstance(saved_service, dict) and saved_service.get("version") == 1:
        from .service_configuration import validate_service_payload, is_service
        if data.get("catalog_kind") == "service" or facility and is_service(facility):
            return validate_service_payload(data, facility=facility)
    data = dict(data)
    existing_workflow = dict(facility.workflow_config or {}) if facility else {}
    if facility:
        # Omitted update fields keep their actual stored values; explicit blanks clear.
        stored = {"name": facility.facility_name, "facility_type": facility.facility_type,
            "location": facility.location, "description": facility.description, "capacity": facility.capacity,
            "rate": str(facility.rate), "mode": facility.booking_mode, "price_type": facility.price_type,
            "rooms_units": facility.rooms_units, "room_type": facility.room_type, "amenities": facility.amenities,
            "status": facility.availability_status, "requirements": facility.requirements, "terms_conditions": facility.terms_conditions}
        data = {**stored, **data}
    errors = {}
    facility_type = str(data.get("facility_type") or "").strip().lower()
    config = FACILITY_TYPE_CONFIG.get(facility_type)
    if config is None:
        errors["facility_type"] = "Select a valid facility type."
        config = FACILITY_TYPE_CONFIG["other"]

    name = str(data.get("name") or "").strip()
    location = str(data.get("location") or "").strip()
    if len(name) > 150:
        errors["name"] = "Use at most 150 characters for the name."
    if len(location) > 180:
        errors["location"] = "Use at most 180 characters for the location."
    if not name:
        errors["name"] = "Facility name is required."
    if not location:
        errors["location"] = "Location is required."

    expected_mode = config["booking_mode"]
    booking_mode = str(data.get("mode") or expected_mode).strip().lower()
    if facility_type == "other" and not str(data.get("mode") or "").strip():
        errors["mode"] = "Select the applicable booking mode for Other."
    physical = facility_type not in {"food_analysis", "training_kitchen", "lease_space"} and booking_mode != "direct"
    if physical and booking_mode not in {"slot", "room", "daily", "custom"}:
        errors["mode"] = "Select Slot-Based, Room / Stay-Based, Daily or Custom."
    elif not physical and booking_mode != expected_mode and not (facility and booking_mode == facility.booking_mode == "direct"):
        errors["mode"] = (
            f"{config['label']} must use {BOOKING_MODE_LABELS[expected_mode]}."
        )

    status = normalize_facility_status(data.get("status"))
    valid_statuses = {choice[0] for choice in STATUS_CHOICES}
    if status not in valid_statuses:
        errors["status"] = "Select a valid facility status."

    price_type = str(data.get("price_type") or ("" if physical else config["default_price_type"])).strip().lower()
    if price_type not in (PRICING_METHODS if physical else config["price_types"]):
        allowed = ", ".join(PRICE_TYPE_LABELS[item] for item in config["price_types"])
        errors["price_type"] = "Select a valid pricing method." if physical else f"{config['label']} supports only: {allowed}."

    required_fields = set(config.get("required", []))
    visible_fields = set(config.get("fields", []))
    if physical:
        visible_fields = {"capacity", "rate", "amenities", "operating_hours"}
        required_fields = {"rate"} if price_type != "custom" else set()
        if booking_mode == "room":
            visible_fields.update({"rooms_units", "room_type", "capacity_per_room", "check_in_time", "check_out_time"})
        elif booking_mode == "slot":
            visible_fields.add("minimum_booking_duration")
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
        errors["amenities"] = "Facility features or services must be a list."
        amenities = []
    if any(not isinstance(item, str) or len(item.strip()) > 200 for item in amenities):
        errors["amenities"] = "Each feature or service must be text of at most 200 characters."
        amenities = []
    amenities = list(dict.fromkeys(item.strip() for item in amenities if item.strip()))
    if "amenities" in required_fields and not amenities:
        errors["amenities"] = "Add at least one service offered."

    raw_workflow = data.get("workflow_config", {})
    if raw_workflow is None:
        raw_workflow = {}
    if not isinstance(raw_workflow, dict):
        errors["workflow_config"] = "Facility workflow details are invalid."
        raw_workflow = {}
    if physical and "equipment" in raw_workflow:
        errors["equipment"] = "Use Facility Features and Optional Additional Fees instead of separate equipment configuration."
    # Preserve unowned saved settings; validate owned settings after merging.
    raw_workflow = {**existing_workflow, **raw_workflow}
    if physical:
        amenities, other_feature = validate_features(amenities, raw_workflow, existing_workflow, errors)
    custom_type = ""
    category_label = "facility category" if physical else "facility type"
    if facility_type == "other":
        value = data.get("custom_facility_type", raw_workflow.get("custom_facility_type", ""))
        if not isinstance(value, str):
            errors["custom_facility_type"] = f"Enter a valid {category_label}."
        else:
            custom_type = value.strip()
            # Older partial-update clients must not lose unrelated saved data.
            submitted_workflow = data.get("workflow_config")
            legacy_omission = (facility and facility.facility_type == "other"
                and "custom_facility_type" not in data
                and (not isinstance(submitted_workflow, dict) or "custom_facility_type" not in submitted_workflow))
            if not custom_type and not legacy_omission:
                required_label = "Specify Facility Category" if physical else "Specify Facility Type"
                errors["custom_facility_type"] = f"{required_label} is required when Other is selected."
            elif custom_type and (len(custom_type) > 120 or not any(char.isalnum() for char in custom_type)
                    or any(char in "<>" or unicodedata.category(char).startswith("C") for char in custom_type)):
                errors["custom_facility_type"] = f"Enter a plain-text {category_label} of up to 120 characters."
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
            except ValidationError as error:
                errors["operating_hours"] = error.messages[0]
        elif isinstance(hours, str) and hours.strip():
            # Older clients may still send text. Normalize only when unambiguous.
            parsed_hours = weekly_hours(hours)
            if parsed_hours is not None:
                workflow_config["operating_hours"] = parsed_hours
            elif facility and hours == existing_workflow.get("operating_hours"):
                workflow_config["operating_hours"] = hours
            else:
                errors["operating_hours"] = "Use the Monday–Sunday schedule controls."
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

    for field in ("capacity_per_room",):
        if field in workflow_config:
            value = _positive_integer(workflow_config[field], field, errors)
            workflow_config[field] = str(value)
    for field in ("check_in_time", "check_out_time"):
        if field in workflow_config:
            try:
                workflow_config[field] = parse_time(workflow_config[field]).strftime("%H:%M")
            except ValidationError:
                errors[field] = "Enter a valid time."
    owned = WORKFLOW_CONFIG_FIELDS | set(RULE_FIELDS) | {"capacity_min", "booking_form_type", "pricing", "damage_deposit", "additional_fees", "custom_facility_type", "discount_rules"}
    if physical:
        owned |= {"other_feature"}
    workflow_config = {**{key: value for key, value in existing_workflow.items() if key not in owned}, **workflow_config}
    if custom_type:
        workflow_config["custom_facility_type"] = custom_type
    if physical:
        if other_feature is not None:
            workflow_config["other_feature"] = other_feature
        workflow_config.update(validate_rental_options(raw_workflow, mode=booking_mode,
            rate=rate, price_type=price_type, capacity=capacity, errors=errors,
            facility_type=facility_type, legacy=bool(facility)))
    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "facility_type": facility_type,
        "location": location,
        "description": str(data.get("description") or "").strip(),
        "capacity": capacity if "capacity" in visible_fields else 0,
        "rate": rate if rate is not None and price_type != "custom" else Decimal("0"),
        "price_type": price_type,
        "booking_mode": booking_mode,
        "rooms_units": (rooms_units or None) if "rooms_units" in visible_fields else None,
        "room_type": room_type if "room_type" in visible_fields else None,
        "amenities": amenities if "amenities" in visible_fields else [],
        "availability_status": status,
        "requirements": str(data.get("requirements") or "").strip(),
        "terms_conditions": str(data.get("terms_conditions") or "").strip(),
        "workflow_config": workflow_config,
    }
