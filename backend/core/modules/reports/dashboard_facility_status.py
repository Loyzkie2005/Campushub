"""Current operational facility states, independent of reservation occupancy."""
from api.models import Facility
from modules.facilities.services.facility_configuration import normalize_facility_status


def facility_operational_status(facilities):
    """Reuse already-loaded facilities: no extra query, no inferred slot status."""
    counts = dict.fromkeys(dict(Facility.STATUS_CHOICES), 0)
    total = 0
    for facility in facilities:
        total += 1
        # Archiving disables booking even if the old status value was left open.
        if facility.is_archived:
            status = Facility.STATUS_INACTIVE
        else:
            raw = facility.availability_status
            if not raw or not str(raw).strip():
                return {"state": "error"}
            status = normalize_facility_status(raw)
        if status not in counts:
            # Unknown stored values must not become made-up zero/open counts.
            return {"state": "error"}
        counts[status] += 1
    return {"state": "ready" if total else "empty", "total": total,
            "rows": [{"key": key, "label": label, "count": counts[key]}
                     for key, label in Facility.STATUS_CHOICES]}
