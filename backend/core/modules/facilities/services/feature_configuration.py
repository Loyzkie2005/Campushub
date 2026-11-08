"""Provided facility features stored in existing amenities/workflow fields."""
import unicodedata

from django.core.exceptions import ValidationError

FEATURES = ["Bleachers", "Restrooms", "Parking Area", "Lighting", "Air Conditioning", "Fans", "Stage",
    "Chairs", "Tables", "Sound System", "Projector", "Microphone", "Bedding", "Pickleball Net"]


def plain_text(value, maximum):
    return (isinstance(value, str) and bool(value.strip()) and len(value.strip()) <= maximum
        and any(c.isalnum() for c in value)
        and not any(c in "<>" or unicodedata.category(c).startswith("C") for c in value))


def booking_requirement_options(facility):
    """Reuse the admin's saved selections, including its resolved custom label."""
    return list(dict.fromkeys(value.strip() for value in (facility.amenities or [])
                             if plain_text(value, 200)))


def validate_booking_requirements(facility, requirements):
    """Validate new requests against this facility, not a universal item list."""
    allowed = set(booking_requirement_options(facility))
    if not isinstance(requirements, list) or any(
        not isinstance(item, str) or item not in allowed for item in requirements
    ):
        raise ValidationError("Additional requirements changed or are not offered by this facility. Return to Select Schedule and review the current options.")
    return list(dict.fromkeys(requirements))


def validate_features(amenities, raw, existing, errors):
    """Return the feature list and identified Other text; null clears previous text."""
    other = raw.get("other_feature")
    if "Other" in amenities and other is None:
        errors["other_feature"] = "Specify Other Feature is required when Other is selected."
    amenities = [value for value in amenities if value != "Other"]
    previous = existing.get("other_feature")
    if previous and previous != other:
        amenities = [value for value in amenities if value != previous]
    if other is not None:
        if not plain_text(other, 200):
            errors["other_feature"] = "Specify Other Feature is required (plain text, up to 200 characters)."
        else:
            other = other.strip()
            amenities = list(dict.fromkeys([*amenities, other]))
    return amenities, other
