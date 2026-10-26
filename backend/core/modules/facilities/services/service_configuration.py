"""Service configuration on existing Facility fields and workflow JSON, not transactions."""
from decimal import Decimal
from datetime import date

from django.core.exceptions import ValidationError

from .catalog import SERVICE_TYPES, SERVICE_MODES
from .operating_schedule import validate_weekly_hours, parse_time
from .rental_configuration import number

CATEGORIES = {"food_analysis": "Laboratory Food Analysis", "training_kitchen": "BPP NC II Assessment",
              "lease_space": "Lease / Commercial Space", "other": "Other"}
REQUEST_TYPES = {"service": "Service Request", "assessment": "Assessment Registration", "lease": "Lease Application"}
SCHEDULING_METHODS = {"specific_date": "Specific Date / Schedule", "admin_assigned": "Admin-Assigned Schedule",
                      "none": "No Scheduled Appointment"}
STATUSES = {"available": "Active", "unavailable": "Temporarily Unavailable", "inactive": "Inactive"}
PRICING = {"analysis": "Per Analysis / Per Sample", "candidate": "Per Candidate", "monthly": "Per Month",
           "sqm": "Per sqm / Month", "machine_month": "Per Machine / Month", "fixed": "Fixed Rate", "custom": "Custom / Subject to Agreement",
           "fixed_monthly": "Fixed Monthly Rental", "term": "Regular Term / Midyear Rate"}
CHARGING_BASES = {"analysis": "Per Analysis", "sample": "Per Sample"}
LEASE_PRICING = ("fixed_monthly", "monthly", "machine_month", "sqm", "term", "custom", "fixed")
PAYMENT_TIMING = {"": "Select payment timing", "before": "Before Processing", "after": "After Processing",
                  "approval": "Upon Approval", "agreement": "According to Agreement",
                  "billing": "After Billing / Statement of Account", "custom": "Custom"}
OUTPUTS = {"none": "None", "analysis_certificate": "Certificate of Analysis", "assessment_result": "Assessment Result / Certification",
           "lease_contract": "Contract of Lease", "custom": "Custom"}
LEASE_TYPES = {"canteen": "Cafeteria / Canteen", "stall": "Food Stall", "vendo": "Wi-Fi Vendo Machine Space",
               "printing": "Photocopying / Printing Machine Space", "other": "Other Commercial Space"}
ALLOWED_PRICING = {"food_analysis": ("analysis", "fixed", "custom"), "training_kitchen": ("candidate", "fixed", "custom"),
                   "lease_space": LEASE_PRICING, "other": tuple(PRICING)}


def is_service(resource):
    return resource.facility_type in SERVICE_TYPES or resource.booking_mode in SERVICE_MODES


def service_configuration_choices():
    return {"categories": CATEGORIES, "request_types": REQUEST_TYPES, "statuses": STATUSES, "pricing": PRICING,
            "payment_timing": PAYMENT_TIMING, "outputs": OUTPUTS, "lease_types": LEASE_TYPES,
            "allowed_pricing": ALLOWED_PRICING, "scheduling_methods": SCHEDULING_METHODS,
            "charging_bases": CHARGING_BASES, "lease_pricing": LEASE_PRICING}


def service_document_requirements(category, request_type):
    """Workflow policy, never an admin-entered catalog switch or a document creation."""
    return {"job_order_required": category == "food_analysis" or (
                category == "training_kitchen" and request_type == "assessment"),
            "soa_required": category == "food_analysis", "contract_required": category == "lease_space"}


def service_pricing_label(resource):
    config = (resource.workflow_config or {}).get("service", {})
    if resource.facility_type == 'lease_space' and config.get('lease_space_details'):
        configured = sum(bool(item.get('pricing_method')) for item in config['lease_space_details'].values())
        if configured:
            return f"{configured} configured space {'rate' if configured == 1 else 'rates'}"
    if resource.price_type == "analysis":
        count = sum(item.get("active") is True for item in config.get("pricing_items", []))
        return f"{count} active analysis {'rate' if count == 1 else 'rates'}"
    method = PRICING.get(resource.price_type)
    if not method:
        return f"\u20b1{resource.rate:,.2f} / service" if resource.price_type == "service" else "Pricing needs configuration"
    if resource.price_type == "custom" and not config.get("custom_amount_set"):
        return "Custom pricing"
    if resource.price_type == 'term':
        rates = config.get('term_rates', {})
        return f"Regular \u20b1{Decimal(rates.get('regular', resource.rate)):,.2f} / Midyear \u20b1{Decimal(rates.get('midyear', '0')):,.2f}"
    if resource.price_type in ("fixed", "custom", "fixed_monthly"):
        return f"\u20b1{resource.rate:,.2f} \u00b7 {method}"
    return f"\u20b1{resource.rate:,.2f} / {dict(candidate='candidate',monthly='month',sqm='m\u00b2',machine_month='machine / month')[resource.price_type]}"


def validate_service_payload(data, *, facility=None):
    """Validate the complete service editor payload; preserve unknown historical settings."""
    errors = {}
    if facility and not is_service(facility):
        raise ValidationError({"service_category": "Use Edit Facility for this physical facility."})
    if facility and facility.is_archived:
        raise ValidationError({'status': 'Restore this service before changing its configuration or status.'})
    previous = dict(facility.workflow_config or {}) if facility else {}
    amount_submitted = "rate" in data
    capacity_submitted = "capacity" in data
    saved_config = previous.get("service", {})
    saved_config = saved_config if isinstance(saved_config, dict) else {}
    if facility:
        stored = {"name": facility.facility_name, "facility_type": facility.facility_type,
                  "custom_facility_type": facility.custom_facility_type, "location": facility.location,
                  "status": facility.availability_status, "mode": facility.booking_mode,
                  "price_type": facility.price_type, "rate": str(facility.rate), "capacity": facility.capacity,
                  "description": facility.description or "", "requirements": facility.requirements or "",
                  "terms_conditions": facility.terms_conditions or ""}
        data = {**stored, **data}
    workflow = data.get("workflow_config", {})
    if not isinstance(workflow, dict) or not isinstance(workflow.get("service", {}), dict):
        raise ValidationError({"configuration": "Service configuration must be an object."})
    raw = {**saved_config, **workflow.get("service", {})}
    workflow = {**previous, **workflow}

    def text(value, field, maximum=500, required=False):
        if not isinstance(value, str):
            errors[field] = "Enter text for this field."
            return ""
        value = value.strip()
        if required and not value or len(value) > maximum:
            errors[field] = f"Enter {'a value using ' if required else ''}at most {maximum} characters."
        return value

    def choice(value, choices, field):
        if not isinstance(value, str) or value not in choices:
            errors[field] = "Select a valid option."
            return next(iter(choices))
        return value

    def flag(key):
        value = raw.get(key, False)
        if not isinstance(value, bool):
            errors[key] = "Use a valid checkbox value."
            return False
        return value

    def money(value, key, required=False):
        parsed = number(value, key, errors, required=required)
        if parsed is not None and parsed != parsed.quantize(Decimal('0.01')):
            errors[key] = 'Use at most two decimal places.'
        return str(parsed) if parsed is not None else ''

    category = choice(data.get("facility_type", ""), CATEGORIES, "service_category")
    name = text(data.get("name", ""), "name", 150, True)
    custom_category = text(data.get("custom_facility_type", ""), "custom_service_category", 120, True) if category == "other" else ""
    request_type = choice(data.get("mode", ""), REQUEST_TYPES, "request_type")
    status = choice(data.get("status", ""), STATUSES, "status")
    method = choice(data.get("price_type", ""), ALLOWED_PRICING[category], "pricing_method")
    approval = workflow.get("requires_approval", False)
    if not isinstance(approval, bool):
        errors["requires_approval"] = "Use a valid checkbox value."
    timing = choice(raw.get("payment_timing", ""), PAYMENT_TIMING, "payment_timing")
    output = choice(raw.get("output_type", ""), {"": "Unspecified", **OUTPUTS}, "output_type")
    service = {"version": 1, "payment_timing": timing, "output_type": output,
               "availability_enabled": flag("availability_enabled")}
    # Preserve historical compatibility values; callers cannot edit document policy here.
    for key, required in service_document_requirements(category, request_type).items():
        service[key] = saved_config.get(key, required)
    if timing == "custom":
        service["custom_payment_timing"] = text(raw.get("custom_payment_timing", ""), "custom_payment_timing", 250, True)
    if output == "custom":
        service["custom_output_type"] = text(raw.get("custom_output_type", ""), "custom_output_type", 150, True)

    rate = Decimal("0")
    if method == "analysis":
        items = raw.get("pricing_items", [])
        if not isinstance(items, list) or not 1 <= len(items) <= 100:
            errors["pricing_items"] = "Add between 1 and 100 analysis/test rates."
            items = []
        service["pricing_items"] = []
        seen = set()
        for index, item in enumerate(items):
            key = f"pricing_items.{index}"
            if not isinstance(item, dict):
                errors[key] = "Enter a valid analysis/test row."
                continue
            title = text(item.get("name", ""), key+".name", 150, True)
            if title.casefold() in seen:
                errors[key+".name"] = "Use a unique analysis/test name."
            seen.add(title.casefold())
            fee = number(item.get("fee"), key+".fee", errors, required=True)
            if fee is not None and fee != fee.quantize(Decimal("0.01")):
                errors[key+".fee"] = "Use at most two decimal places."
            active = item.get("active", False)
            if not isinstance(active, bool):
                errors[key+".active"] = "Use a valid checkbox value."
            service["pricing_items"].append({"name": title, "description": text(item.get("description", ""), key+".description", 500),
                "fee": str(fee or 0), "active": active,
                "charging_basis": choice(item.get('charging_basis', 'analysis'), CHARGING_BASES, key+'.charging_basis')})
    elif method == 'term':
        terms = raw.get('term_rates', {})
        if not isinstance(terms, dict):
            errors['term_rates'] = 'Configure regular term and midyear rates.'
            terms = {}
        service['term_rates'] = {key: money(terms.get(key), 'term_rates.'+key, True) for key in ('regular', 'midyear')}
        rate = Decimal(service['term_rates']['regular'] or '0')
    else:
        if method == "custom":
            service["custom_pricing_description"] = text(raw.get("custom_pricing_description", ""), "custom_pricing_description", 1000, True)
        amount = data.get("rate")
        if method == "custom" and not amount_submitted and not (facility and facility.price_type == "custom" and saved_config.get("custom_amount_set")):
            amount = ""
        rate = number(amount, "rate", errors, required=method != "custom") or Decimal("0")
        service["custom_amount_set"] = method == "custom" and amount not in (None, "")
        if rate != rate.quantize(Decimal("0.01")):
            errors["rate"] = "Use at most two decimal places."

    owned = {"service", "requires_approval", "custom_facility_type", "operating_hours", "turnaround_information", "assessment_service_type"}
    cleaned_workflow = {key: value for key, value in previous.items() if key not in owned}
    cleaned_workflow.update(service=service, requires_approval=approval)
    if custom_category:
        cleaned_workflow["custom_facility_type"] = custom_category
    if service["availability_enabled"]:
        try:
            hours = workflow.get("operating_hours")
            if not isinstance(hours, dict):
                raise ValidationError("Configure available days with start/end times.")
            hours = validate_weekly_hours(hours)
            saved_enabled = saved_config.get("availability_enabled") is True or (
                saved_config.get("version") != 1 and isinstance(previous.get("operating_hours"), dict))
            unchanged_closed = saved_enabled and hours == previous.get("operating_hours")
            if not any(hours.values()) and not unchanged_closed:
                raise ValidationError("Select at least one available day, or turn off weekly availability.")
            cleaned_workflow["operating_hours"] = hours
        except ValidationError as error:
            errors["operating_hours"] = error.messages[0]
    capacity = 0
    if category == "food_analysis":
        service["sample_acceptance_required"] = flag("sample_acceptance_required")
        cleaned_workflow["turnaround_information"] = text(workflow.get("turnaround_information", ""), "turnaround_information", 250)
    elif category == "training_kitchen":
        raw_capacity = data.get("capacity")
        # Existing zero means unconfigured; an explicitly entered zero is invalid.
        if not capacity_submitted and raw_capacity == 0:
            raw_capacity = None
        capacity = number(raw_capacity, "candidate_capacity", errors, integer=True, maximum=Decimal("1000000"))
        if capacity is not None and capacity <= 0:
            errors["candidate_capacity"] = "Enter a positive whole number, or leave candidate capacity blank."
        capacity = capacity or 0
        cleaned_workflow["assessment_service_type"] = text(workflow.get("assessment_service_type", ""), "assessment_service_type", 150)
        service["scheduling_method"] = choice(raw.get("scheduling_method", ""), SCHEDULING_METHODS, "scheduling_method")
        if service['scheduling_method'] == 'specific_date':
            dates = raw.get('assessment_dates', [])
            if not isinstance(dates, list) or len(dates) > 100:
                errors['assessment_dates'] = 'Use at most 100 assessment schedules.'
                dates = []
            service['assessment_dates'] = []
            seen = set()
            for index, item in enumerate(dates):
                key = f'assessment_dates.{index}'
                try:
                    if not isinstance(item, dict): raise ValueError
                    day = date.fromisoformat(item.get('date', '')).isoformat()
                    start, end = item.get('start') or '', item.get('end') or ''
                    if start or end:
                        start, end = parse_time(start).strftime('%H:%M'), parse_time(end).strftime('%H:%M')
                        if start >= end: raise ValueError
                    if (day, start, end) in seen: raise ValueError
                    seen.add((day, start, end))
                    service['assessment_dates'].append({'date': day, 'start': start, 'end': end})
                except (ValueError, TypeError, ValidationError):
                    errors[key] = 'Enter a unique valid assessment date and optional opening/closing times in order.'
        # Legacy checkbox history is retained; the explicit method is authoritative.
        service["schedule_required"] = saved_config.get("schedule_required", service["scheduling_method"] != "none")
    elif category == "lease_space":
        spaces = raw.get("lease_space_types", [])
        if not isinstance(spaces, list) or any(not isinstance(item, str) or item not in LEASE_TYPES for item in spaces):
            errors["lease_space_types"] = "Select valid lease space types."
            spaces = []
        service["lease_space_types"] = sorted(set(spaces))
        if "other" in spaces:
            service["other_lease_space_type"] = text(raw.get("other_lease_space_type", ""), "other_lease_space_type", 150, True)
        details = raw.get('lease_space_details', {})
        if not isinstance(details, dict):
            errors['lease_space_details'] = 'Enter valid lease space settings.'
            details = {}
        service['lease_space_details'] = {}
        for space in service['lease_space_types']:
            item = details.get(space, {})
            if not isinstance(item, dict):
                errors['lease_space_details.'+space] = 'Enter valid lease space settings.'
                continue
            key = 'lease_space_details.'+space
            cleaned = {field: text(item.get(field, ''), key+'.'+field, 1000 if field=='utility_conditions' else 250)
                       for field in ('location', 'electricity_arrangement', 'internet_arrangement', 'utility_conditions')}
            for field in ('available_area', 'standard_area', 'water_charge'):
                cleaned[field] = money(item.get(field), key+'.'+field)
            pricing = choice(item.get('pricing_method', ''), ('', *LEASE_PRICING), key+'.pricing_method')
            cleaned['pricing_method'] = pricing
            if pricing == 'term':
                for field in ('regular_term_rate', 'midyear_rate'):
                    cleaned[field] = money(item.get(field), key+'.'+field, True)
            elif pricing:
                cleaned['rate'] = money(item.get('rate'), key+'.rate', pricing!='custom')
            if pricing == 'custom':
                cleaned['pricing_description'] = text(item.get('pricing_description', ''), key+'.pricing_description', 1000, True)
            service['lease_space_details'][space] = cleaned
    if "schedule_required" in saved_config:
        service["schedule_required"] = saved_config["schedule_required"]
    result = {"name": name, "facility_type": category, "location": text(data.get("location", ""), "location", 180),
              "description": text(data.get("description", ""), "description", 5000), "booking_mode": request_type,
              "availability_status": status, "price_type": method, "rate": rate, "capacity": int(capacity),
              "rooms_units": facility.rooms_units if facility else None, "room_type": facility.room_type if facility else "",
              "amenities": list(facility.amenities or []) if facility else [], "workflow_config": cleaned_workflow,
              "requirements": text(data.get("requirements", ""), "requirements", 5000),
              "terms_conditions": text(data.get("terms_conditions", ""), "terms_conditions", 10000)}
    if errors:
        raise ValidationError(errors)
    return result
