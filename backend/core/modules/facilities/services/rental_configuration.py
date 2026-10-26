"""Rental configuration stored in the existing Facility fields/workflow JSON."""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from .feature_configuration import plain_text

PRICING_METHODS = {
    "hour": "Per Hour", "base_hour": "Base Duration + Additional Hour",
    "day": "Per Day", "person": "Per Person", "person_night": "Per Person / Per Night",
    "night": "Per Night", "session": "Fixed Rate", "custom": "Custom",
}
FORM_TYPES = {
    "rental": "Facilities and Spaces Rental Booking Slip",
    "accommodation": "Room Accommodation Booking Slip",
    "general": "Custom / General Booking Form",
}
FORM_DEFAULTS = {"covered_court": "rental", "function_hall": "rental", "hostel": "accommodation"}


def booking_form_for_category(facility_type, workflow=None):
    """Resolve the canonical physical slip; Other retains its explicit/legacy choice."""
    form = FORM_DEFAULTS.get(facility_type) or (workflow or {}).get("booking_form_type", "general")
    if not isinstance(form, str) or form not in FORM_TYPES:
        raise ValidationError("The facility booking form needs configuration.")
    return form


def booking_slip_label(facility, quote=None, workflow_snapshot=None):
    """Keep the saved booking's form label; only unsnapshotted slips use current config."""
    if (quote or {}).get("form_label"):
        return quote["form_label"]
    saved_form = workflow_snapshot.get("booking_form_type") if isinstance(workflow_snapshot, dict) else None
    if isinstance(saved_form, str) and saved_form in FORM_TYPES:
        return FORM_TYPES[saved_form]
    try:
        return FORM_TYPES[booking_form_for_category(facility.facility_type if facility else "",
                                                   facility.workflow_config if facility else {})]
    except ValidationError:
        return "Booking Slip"  # Preserve printing of legacy unconfigured records.

FEE_UNITS = {"item": "Per Item", "hour": "Per Hour", "booking": "Per Booking", "day": "Per Day", "night": "Per Night", "person": "Per Person", "fixed": "Fixed", "custom": "Custom"}
RULE_FIELDS = ("requires_approval", "requires_pre_use_inspection", "requires_post_use_inspection", "damage_deposit_applicable")
DISCOUNT_CLIENTS = {"internal": "Internal Client", "immediate_family": "Immediate Family", "student": "USTP Student", "other": "Other"}
DISCOUNT_TYPES = {"percentage": "Percentage", "fixed": "Fixed Amount"}
DISCOUNT_SCOPES = {"rental_fee": "Rental Fee", "base_rate": "Base Rate", "additional_hour_rate": "Additional Hour Rate", "individual_rate": "Individual Rate", "partner_rate": "Partner / Shared Room Rate", "entire_rental_rate": "Entire Rental Rate", "custom": "Custom"}
DISCOUNT_SCOPE_METHODS = {
    **{method: ("rental_fee", "entire_rental_rate", "custom") for method in ("hour", "day", "person", "night", "session")},
    "base_hour": ("base_rate", "additional_hour_rate", "entire_rental_rate", "custom"),
    "person_night": ("individual_rate", "partner_rate", "entire_rental_rate", "custom"),
    "custom": ("entire_rental_rate", "custom"),
}


def validate_discount_rules(rules, *, price_type, errors, pricing=None):
    """Validate saved configuration, without calculating client eligibility or charges."""
    if not isinstance(rules, list) or len(rules) > 30:
        errors["discount_rules"] = "Use a list with at most 30 discount rules."
        return []
    cleaned = []
    for index, rule in enumerate(rules):
        key = f"discount_rules.{index}"
        if not isinstance(rule, dict):
            errors[key] = "Enter valid discount rule details."
            continue
        client, kind, scope = (rule.get(field) for field in ("eligible_client_type", "discount_type", "applies_to"))
        if not isinstance(client, str) or client not in DISCOUNT_CLIENTS:
            errors[key] = "Select an eligible client type."
        if not isinstance(kind, str) or kind not in DISCOUNT_TYPES:
            errors[key] = "Select Percentage or Fixed Amount."
        if not isinstance(scope, str) or scope not in DISCOUNT_SCOPE_METHODS.get(price_type, ()):
            errors[key] = "Select a discount scope supported by the selected pricing method."
        elif scope == "partner_rate" and (pricing or {}).get("partner_rate") is None:
            errors[key] = "Configure the Partner / Shared Room Rate before targeting it with a discount."
        value = number(rule.get("discount_value"), key, errors, required=True,
            maximum=Decimal("100") if kind == "percentage" else Decimal("99999999.99"))
        active = rule.get("active", True)
        if not isinstance(active, bool):
            errors[key] = "Choose a valid active setting."
        item = {"eligible_client_type": client, "discount_type": kind,
            "discount_value": str(value) if value is not None else "", "applies_to": scope, "active": active}
        if scope == "custom":
            detail = rule.get("custom_scope", "")
            if not isinstance(detail, str) or not detail.strip() or len(detail.strip()) > 200 or any(char in "<>\r\n\x00" for char in detail):
                errors[key] = "Describe the custom discount application in plain text (up to 200 characters)."
            else:
                item["custom_scope"] = detail.strip()
        cleaned.append(item)
    return cleaned


def number(value, field, errors, *, required=False, integer=False, maximum=Decimal("99999999.99")):
    """Reject malformed/nonfinite numbers instead of stripping their characters."""
    if value in (None, ""):
        if required:
            errors[field] = "This value is required."
        return None
    try:
        if isinstance(value, bool):
            raise ValueError
        parsed = Decimal(str(value))
        if not parsed.is_finite() or parsed < 0 or parsed > maximum:
            raise ValueError
        if integer and parsed != parsed.to_integral_value():
            raise ValueError
        if not integer and parsed.as_tuple().exponent < -2:
            raise ValueError
        return int(parsed) if integer else parsed
    except (InvalidOperation, ValueError, TypeError):
        errors[field] = "Enter a non-negative whole number." if integer else "Enter a valid non-negative amount with up to two decimal places."
        return None


def validate_rental_options(raw, *, mode, rate, price_type, capacity, errors, facility_type, legacy=False):
    """Return sanitized additional settings; no database or transaction writes."""
    result = {}
    minimum = number(raw.get("capacity_min"), "capacity_min", errors, integer=True, maximum=Decimal("2147483647"))
    if minimum is not None:
        if not capacity or minimum > capacity:
            errors["capacity_min"] = "Minimum capacity must not exceed maximum capacity."
        result["capacity_min"] = minimum
    for key in RULE_FIELDS:
        default = key == "requires_approval" or (not legacy and facility_type in FORM_DEFAULTS
            and key in ("requires_pre_use_inspection", "requires_post_use_inspection"))
        value = raw.get(key, default)
        if not isinstance(value, bool):
            errors[key] = "Choose Yes or No."
        else:
            result[key] = value
    suggested_form = FORM_DEFAULTS.get(facility_type, "")
    form_type = suggested_form or raw.get("booking_form_type", "")
    if not form_type and legacy and "booking_form_type" not in raw:
        pass  # Preserve unrelated edits to older unconfigured records.
    else:
        try:
            result["booking_form_type"] = booking_form_for_category(facility_type, {"booking_form_type": form_type})
        except ValidationError:
            errors["booking_form_type"] = "Select a valid booking form type."
    if price_type not in PRICING_METHODS:
        errors["price_type"] = "Select a valid pricing method."
    if price_type != "custom" and rate is None:
        errors["rate"] = "Enter the rate for the selected pricing method."
    pricing = raw.get("pricing", {})
    if not isinstance(pricing, dict):
        errors["pricing"] = "Pricing configuration must be an object."
        pricing = {}
    cleaned_pricing = {}
    if price_type == "base_hour":
        hours = number(pricing.get("base_duration"), "base_duration", errors, required=True, maximum=Decimal("24"))
        extra = number(pricing.get("additional_hour_rate"), "additional_hour_rate", errors, required=True)
        if hours is not None:
            if hours <= 0:
                errors["base_duration"] = "Base duration must be greater than zero and at most 24 hours."
            cleaned_pricing["base_duration"] = str(hours)
        if extra is not None:
            cleaned_pricing["additional_hour_rate"] = str(extra)
    if price_type == "custom":
        notes = str(pricing.get("notes") or "").strip()
        if not notes or len(notes) > 2000:
            errors["pricing_notes"] = "Describe the custom pricing method (up to 2,000 characters)."
        cleaned_pricing["notes"] = notes
    if price_type == "person_night" and pricing.get("partner_rate") not in (None, ""):
        partner = number(pricing.get("partner_rate"), "partner_rate", errors, required=True)
        occupancy = number(pricing.get("partner_occupancy_required"), "partner_occupancy_required", errors,
            required=True, integer=True, maximum=Decimal("2147483647"))
        if occupancy is not None and occupancy < 2:
            errors["partner_occupancy_required"] = "Shared-room occupancy must be at least two guests in the same room."
        if partner is not None:
            cleaned_pricing["partner_rate"] = str(partner)
        if occupancy is not None:
            cleaned_pricing["partner_occupancy_required"] = occupancy
    if cleaned_pricing:
        result["pricing"] = cleaned_pricing
    if result.get("damage_deposit_applicable"):
        deposit = raw.get("damage_deposit", {})
        if not isinstance(deposit, dict):
            deposit = {}
        kind = deposit.get("type")
        if kind not in ("fixed", "percentage"):
            errors["damage_deposit_type"] = "Select Fixed Amount or Percentage."
        value = number(deposit.get("value"), "damage_deposit_value", errors, required=True,
                       maximum=Decimal("100") if kind == "percentage" else Decimal("99999999.99"))
        result["damage_deposit"] = {"type": kind, "value": str(value) if value is not None else ""}
    fees = raw.get("additional_fees", [])
    if not isinstance(fees, list) or len(fees) > 30:
        errors["additional_fees"] = "Use a list with at most 30 additional fees."
        fees = []
    clean_fees = []
    for index, fee in enumerate(fees):
        key = f"additional_fees.{index}"
        if not isinstance(fee, dict):
            errors[key] = "Enter valid fee details."
            continue
        name = fee.get("name")
        amount = number(fee.get("amount"), key, errors, required=True)
        unit, active = fee.get("unit"), fee.get("active", True)
        # Preserve the old unit code on existing integrations; new forms use item.
        if not plain_text(name, 150) or not isinstance(unit, str) or unit not in {*FEE_UNITS, "unit"} or not isinstance(active, bool):
            errors[key] = "Enter a fee name, valid charging basis and active setting."
        cleaned = {"name": name.strip() if isinstance(name, str) else "", "amount": str(amount) if amount is not None else "", "unit": unit, "active": active}
        if unit == "custom":
            detail = fee.get("custom_basis")
            if not plain_text(detail, 200):
                errors[f"{key}.custom_basis"] = "Describe the custom charging basis (up to 200 characters)."
            else:
                cleaned["custom_basis"] = detail.strip()
        clean_fees.append(cleaned)
    result["additional_fees"] = clean_fees
    result["discount_rules"] = validate_discount_rules(raw.get("discount_rules", []), price_type=price_type, errors=errors, pricing=cleaned_pricing)
    return result


def capacity_label(facility):
    """Summarize actual accommodation rooms or saved capacity, never guessed units."""
    if facility.booking_mode == "room":
        rooms = getattr(facility, "configured_room_count", None)
        if rooms is None:
            rooms = facility.rooms.count() if not facility._state.adding else 0
        if rooms:
            label = f"{rooms} Room{'s' if rooms != 1 else ''}"
            return f"{label} / {facility.capacity} pax" if facility.capacity else label
    elif facility.booking_mode in {"service", "assessment", "lease", "direct"} and facility.rooms_units:
        return f"{facility.rooms_units} unit{'s' if facility.rooms_units != 1 else ''}"
    maximum = facility.capacity or 0
    minimum = (facility.workflow_config or {}).get("capacity_min")
    if maximum:
        return f"{minimum}–{maximum} pax" if minimum not in (None, "") else f"{maximum} pax"
    return "Not specified"


def pricing_label(facility):
    rate = facility.rate or Decimal("0")
    money = f"₱{rate:,.2f}".removesuffix(".00")
    method = facility.price_type
    pricing = (facility.workflow_config or {}).get("pricing", {})
    if method == "base_hour" and isinstance(pricing, dict):
        try:
            extra = Decimal(str(pricing["additional_hour_rate"]))
            return f"{money} / first {pricing['base_duration']} hrs + ₱{extra:,.2f}/hr".replace(".00/hr", "/hr")
        except (KeyError, InvalidOperation):
            return "Pricing needs review"
    if method == "custom":
        notes = pricing.get("notes", "") if isinstance(pricing, dict) else ""
        if isinstance(notes, str) and notes.strip() and not any(char in "<>" or ord(char) < 32 for char in notes):
            summary = " ".join(notes.split())
            return summary if len(summary) <= 80 else summary[:77] + "…"
        return "Custom quote"
    if method == "person_night" and isinstance(pricing, dict) and pricing.get("partner_rate") is not None:
        try:
            partner = Decimal(str(pricing["partner_rate"]))
            occupancy = int(pricing["partner_occupancy_required"])
            if not partner.is_finite() or partner < 0 or occupancy < 2:
                raise ValueError
            return f"{money} / person / night · shared ₱{partner:,.2f} / person / night ({occupancy} guests in one room)"
        except (InvalidOperation, KeyError, ValueError, TypeError):
            return "Pricing needs review"
    if method == "session":
        return f"{money} fixed"
    suffix = {"hour": "hour", "day": "day", "person_night": "person / night", "person": "person",
              "night": "night", "service": "service", "monthly": "month"}.get(method)
    return f"{money} / {suffix}" if suffix else "Pricing needs review"


def slot_base_amount(facility, hours, *, include_configured_adjustments=False):
    """One rate calculation used by the existing mobile rental quote."""
    if facility.price_type == "base_hour":
        pricing = (facility.workflow_config or {}).get("pricing", {})
        try:
            base = Decimal(str(pricing["base_duration"]))
            extra = Decimal(str(pricing["additional_hour_rate"]))
            if not base.is_finite() or not extra.is_finite() or base <= 0 or extra < 0:
                raise ValueError
        except (KeyError, InvalidOperation, ValueError, TypeError):
            raise ValidationError("The rental pricing configuration needs review by Facilities Admin.")
        amount = facility.rate + max(hours - base, Decimal("0")) * extra
    elif facility.price_type in ("hour", "session"):
        amount = facility.rate * (hours if facility.price_type == "hour" else 1)
    else:
        # No silent hourly/fixed fallback for person/night/custom pricing.
        raise ValidationError("This pricing method requires a quote from Facilities Admin.")
    if include_configured_adjustments:
        return amount.quantize(Decimal("0.01"))
    workflow = facility.workflow_config or {}
    if any(item.get("is_active") and item.get("has_additional_fee") for item in workflow.get("equipment", []) if isinstance(item, dict)):
        raise ValidationError("Equipment charges require a complete quote from Facilities Admin.")
    if workflow.get("damage_deposit_applicable") or any(f.get("active") for f in workflow.get("additional_fees", []) if isinstance(f, dict)):
        raise ValidationError("Deposits or additional charges require a complete quote from Facilities Admin.")
    if any(rule.get("active") for rule in workflow.get("discount_rules", []) if isinstance(rule, dict)):
        raise ValidationError("Discount eligibility requires a complete quote from Facilities Admin.")
    return amount.quantize(Decimal("0.01"))
