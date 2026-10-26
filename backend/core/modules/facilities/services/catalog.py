"""Separate existing service workflows without copying Facility/Booking records."""
from django.db.models import Q

SERVICE_TYPES = ("food_analysis", "training_kitchen", "lease_space")
SERVICE_MODES = ("service", "direct", "assessment", "lease")
SERVICE_LABELS = {
    "food_analysis": ("Laboratory Service", "Service Request"),
    "training_kitchen": ("Training / Assessment Service", "Assessment Registration"),
    "lease_space": ("Leasing Service", "Lease Application"),
}
MODE_LABELS = {
    "service": ("Service", "Service Request"),
    "direct": ("Service", "Service Request"),
    "assessment": SERVICE_LABELS["training_kitchen"],
    "lease": SERVICE_LABELS["lease_space"],
}


def service_resources_q(prefix=""):
    """Reusable ORM condition, optionally through Booking's facility relation."""
    return Q(**{f"{prefix}facility_type__in": SERVICE_TYPES}) | Q(
        **{f"{prefix}booking_mode__in": SERVICE_MODES}
    )


def service_labels(facility):
    """Return presentation labels from existing configured types/modes."""
    from .service_configuration import CATEGORIES, REQUEST_TYPES
    fallback = SERVICE_LABELS.get(facility.facility_type) or MODE_LABELS.get(facility.booking_mode, ("Other", "Service Request"))
    return (facility.custom_facility_type or CATEGORIES.get(facility.facility_type, fallback[0]),
            REQUEST_TYPES.get(facility.booking_mode, fallback[1]))
