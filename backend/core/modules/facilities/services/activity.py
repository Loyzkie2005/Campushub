"""Facility summaries and write hooks backed by the existing AccountActivity table."""
from accounts.activity_logging import log_account_activity
from accounts.models import AccountActivity
from django.utils import timezone
from django.db.models import Q
from .catalog import SERVICE_MODES, SERVICE_TYPES, service_resources_q
from .facility_configuration import STATUS_CHOICES, normalize_facility_status


FACILITY_ACTIVITY_LIMIT = 5
ICON_PATHS = {
    "add": "M12 4.5v15m7.5-7.5h-15",
    "edit": "m16.862 4.487 1.687-1.688a1.875 1.875 0 0 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Z",
    "status": "M16.023 9.348h4.992M2.985 19.644v-4.992m0 0h4.992m-4.993 0a8.25 8.25 0 0 0 13.803 3.7M21.015 9.348A8.25 8.25 0 0 0 7.212 5.648",
    "money": "M12 6v12m3-10.5H10.5a2.25 2.25 0 0 0 0 4.5h3a2.25 2.25 0 0 1 0 4.5H9M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    "calendar": "M6.75 3v2.25m10.5-2.25v2.25M3.75 9h16.5m-15 12h13.5A1.5 1.5 0 0 0 20.25 19.5V6.75a1.5 1.5 0 0 0-1.5-1.5H5.25a1.5 1.5 0 0 0-1.5 1.5V19.5a1.5 1.5 0 0 0 1.5 1.5Z",
    "archive": "M20.25 7.5 19.625 18.132a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5m5.25 4.5h6M3.375 7.5h17.25V3.75H3.375Z",
    "restore": "M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
}
EVENTS = {
    "service_added": ("added", "New Service", "add"),
    "service_updated": ("updated", "Service Update", "edit"),
    "service_status_changed": ("status changed", "Status Change", "status"),
    "service_pricing_updated": ("pricing updated", "Pricing Update", "money"),
    "service_archived": ("archived", "Archive", "archive"),
    "service_reactivated": ("restored", "Restoration", "restore"),
    "facility_block_added": ("schedule block added", "Schedule Block", "calendar"),
    "facility_block_updated": ("schedule block updated", "Schedule Block Update", "calendar"),
    "facility_block_cancelled": ("schedule block cancelled", "Schedule Block Cancellation", "calendar"),
    "facility_added": ("added", "New Facility", "add"),
    "facility_updated": ("updated", "Facility Update", "edit"),
    "facility_archived": ("archived", "Archive", "archive"),
    "facility_reactivated": ("reactivated", "Reactivation", "restore"),
    "facility_status_changed": ("status changed", "Status Change", "status"),
    "facility_pricing_updated": ("pricing updated", "Pricing Update", "money"),
    "facility_discount_updated": ("discount rules updated", "Discount Rules Update", "money"),
    "facility_schedule_updated": ("operating schedule updated", "Schedule Update", "calendar"),
    "facility_features_updated": ("features updated", "Feature Update", "edit"),
    "facility_booking_config_updated": ("booking configuration updated", "Booking Configuration", "calendar"),
    "facility_rooms_updated": ("room/unit configuration updated", "Room / Unit Update", "edit"),
}


def facility_snapshot(facility):
    """Capture owned persisted values before an Edit; no submitted secrets are copied."""
    workflow = facility.workflow_config if isinstance(facility.workflow_config, dict) else {}
    return {
        "status": normalize_facility_status(facility.availability_status),
        "pricing": (facility.rate, facility.price_type, workflow.get("pricing"),
                    workflow.get("additional_fees"), workflow.get("damage_deposit"),
                    (workflow.get('service') or {}).get('pricing_items'), (workflow.get('service') or {}).get('term_rates'),
                    (workflow.get('service') or {}).get('lease_space_details')),
        "discount": workflow.get("discount_rules"),
        "booking": (facility.booking_mode, workflow.get("booking_form_type"), workflow.get("requires_approval"),
                    workflow.get("requires_pre_use_inspection"), workflow.get("requires_post_use_inspection"),
                    workflow.get("damage_deposit_applicable")),
        "schedule": (facility.slots, workflow.get("operating_hours"), workflow.get("minimum_booking_duration")),
        "features": (facility.amenities, workflow.get("other_feature")),
        "rooms": (facility.rooms_units, facility.room_type, workflow.get("capacity_per_room"),
                  workflow.get("check_in_time"), workflow.get("check_out_time")),
        "details": (facility.facility_name, facility.facility_type, facility.location, facility.description,
                    facility.capacity, facility.requirements, facility.terms_conditions,
                    facility.image_url, {key: value for key, value in workflow.items() if key not in {
                        "pricing", "discount_rules", "additional_fees", "damage_deposit", "operating_hours",
                        "minimum_booking_duration", "other_feature", "capacity_per_room", "check_in_time", "check_out_time",
                        "booking_form_type", "requires_approval", "requires_pre_use_inspection", "requires_post_use_inspection",
                        "damage_deposit_applicable"}}),
    }


def record_facility_activity(request, facility, *, action=None, before=None):
    """Write one real event per successful action; unchanged saves/services produce none."""
    service = facility.facility_type in SERVICE_TYPES or facility.booking_mode in SERVICE_MODES
    changed = []
    if before is not None:
        after = facility_snapshot(facility)
        changed = [key for key in after if after[key] != before[key]]
        if not changed:
            return None
        codes = {"status": "facility_status_changed", "pricing": "facility_pricing_updated",
                 "schedule": "facility_schedule_updated", "features": "facility_features_updated",
                 "rooms": "facility_rooms_updated", "discount": "facility_discount_updated",
                 "booking": "facility_booking_config_updated"}
        action = codes.get(changed[0], "facility_updated") if len(changed) == 1 else "facility_updated"
        if service and changed == ['pricing', 'details']:
            action = 'facility_pricing_updated'
    if service:
        action = {'facility_added':'service_added', 'facility_status_changed':'service_status_changed',
            'facility_pricing_updated':'service_pricing_updated', 'facility_archived':'service_archived',
            'facility_reactivated':'service_reactivated'}.get(action, 'service_updated')
    if action not in EVENTS:
        raise ValueError("Unknown facility activity.")
    metadata = {"facility_id": str(facility.pk), "facility_name": facility.facility_name,
                "changed_sections": changed, "resource_kind": "service" if service else "physical"}
    if action in ("facility_status_changed", 'service_status_changed'):
        from .service_configuration import STATUSES
        metadata["status_label"] = (STATUSES if service else dict(STATUS_CHOICES)).get(normalize_facility_status(facility.availability_status), "Inactive")
    title = facility_activity_row_data(action, metadata)["title"]
    return log_account_activity(request, source=AccountActivity.SOURCE_ADMIN, account=request.user,
        module="Services" if service else "Facilities", activity_type=action, activity=title[:180], result=AccountActivity.RESULT_SUCCESS,
        metadata=metadata)


def facility_activity_row_data(action, metadata):
    message, description, icon = EVENTS[action]
    name = str(metadata.get("facility_name") or "Facility")[:150]
    if action in ("facility_status_changed", 'service_status_changed'):
        message = f"status changed to {metadata.get('status_label') or 'Inactive'}"
    return {"kind": "facility", "title": f"{name} {message}.", "description": description,
            "icon_path": ICON_PATHS[icon]}


def facility_activity_row(event):
    """Return only safe display fields, including the actual audit timestamp."""
    if event is None:
        return None
    performer = (event.full_name or "").strip() or (event.username or "").strip()
    if not performer or performer.isdigit():
        performer = "System"
    local_time = timezone.localtime(event.created_at)
    time_label = f"{local_time:%b %d, %Y} • {local_time.strftime('%I:%M %p').lstrip('0')}"
    return {**facility_activity_row_data(event.activity_type, event.metadata), "occurred_at": event.created_at,
            "performed_by": performer, "time_label": time_label}


def recent_facility_activities(*, services=False):
    """Newest five successful physical administrative events, in one bounded query."""
    from api.models import Facility
    if services:
        events = AccountActivity.objects.filter(module='Services', result=AccountActivity.RESULT_SUCCESS,
            activity_type__in=[code for code in EVENTS if code.startswith('service_')]).order_by('-created_at', '-pk')[:FACILITY_ACTIVITY_LIMIT]
        return [facility_activity_row(event) for event in events]
    service_ids = list(Facility.objects.filter(service_resources_q()).values_list("pk", flat=True))
    # Old event codes were written by this physical-only logger. Preserve their
    # snapshots even when the target row is gone; newer entries carry explicit scope.
    events = AccountActivity.objects.filter(module="Facilities", result=AccountActivity.RESULT_SUCCESS,
        activity_type__in=EVENTS).filter(Q(metadata__resource_kind="physical") | Q(metadata__resource_kind__isnull=True))
    events = events.exclude(metadata__facility_id__in=service_ids).order_by("-created_at", "-pk")[:FACILITY_ACTIVITY_LIMIT]
    return [facility_activity_row(event) for event in events]
