"""Structured blocks reuse legacy Booking records and their existing JSON sidecar."""
import base64
import io
from datetime import date, timedelta, time

from django.core.exceptions import ValidationError
from django.db.models import Q
from PIL import Image

from api.models import Booking, FacilityBookingRequest
from .operating_schedule import parse_time

SCHEDULE_TYPES = {"class": "Class / Academic Schedule", "official": "Official Campus Use",
                  "maintenance": "Maintenance", "hold": "Administrative Hold / Unavailable", "other": "Other"}
BLOCK_PREFIXES = ("class", "maintenance", "official", "hold", "other", "blocked", "assessment")


def schedule_blocks_q():
    from .catalog import service_resources_q
    # Missing JSON keys must not turn a negated source comparison into SQL NULL.
    query = Q(pk__in=FacilityBookingRequest.objects.filter(details__source='schedule').values('booking_id'))
    for kind in BLOCK_PREFIXES:
        rule = Q(purpose__iregex=rf"^\s*\[{kind}\]")
        query |= rule & ~service_resources_q("facility__") if kind == "assessment" else rule
    return query


def metadata(booking):
    try:
        return booking.mobile_request.details or {}
    except FacilityBookingRequest.DoesNotExist:
        return {}


def schedule_days(booking, first=None, last=None):
    """Expand dates for display/checking only; never create occurrence records."""
    if not booking.booking_date:
        return
    config = metadata(booking).get("schedule", {})
    finish = date.fromisoformat(config.get("until", booking.booking_date.isoformat()))
    start = max(booking.booking_date, first or booking.booking_date)
    finish = min(finish, last or finish)
    while start <= finish:
        if config.get("repeat") != "weekly" or start.weekday() in config.get("weekdays", []):
            yield start
        start += timedelta(days=1)


def validate_schedule(data):
    kind = data.get("type")
    if kind not in SCHEDULE_TYPES:
        raise ValidationError("Select a valid facility schedule type. Reservations belong in Add Reservation.")
    first = date.fromisoformat(str(data.get("date", "")))
    last = date.fromisoformat(str(data.get("until") or first))
    if last < first or (last - first).days > 366:
        raise ValidationError("Use an end date on or after the start date, within one year.")
    repeat = data.get("repeat", "none")
    days = data.get("weekdays", [])
    if repeat not in ("none", "weekly") or not isinstance(days, list):
        raise ValidationError("Select a valid recurrence.")
    if repeat == "weekly" and (not days or any(type(day) is not int or day not in range(7) for day in days)):
        raise ValidationError("Choose at least one valid weekday.")
    all_day = data.get("all_day", False)
    if not isinstance(all_day, bool):
        raise ValidationError("Choose a valid all-day setting.")
    start, end = (time.min, time(23, 59, 59)) if all_day else (parse_time(data.get("start", "")), parse_time(data.get("end", "")))
    if start >= end:
        raise ValidationError("End time must be later than start time.")
    title = str(data.get("purpose") or data.get("description") or "").strip()
    other = str(data.get("other_type") or "").strip()
    if not title or len(title) > 500 or (kind == "other" and (not other or len(other) > 150)):
        raise ValidationError("Enter a title/description and specify the schedule type when Other is selected.")
    return first, start, end, {"type": kind, "until": last.isoformat(), "repeat": repeat,
        "weekdays": sorted(set(days)) if repeat == "weekly" else [], "all_day": all_day,
        "title": title, "other_type": other if kind == "other" else ""}


PRIVATE_ATTACHMENT_TYPES = ('application/pdf', 'image/png', 'image/jpeg', 'image/webp')


def validated_attachment(data):
    """Store bounded supporting evidence in existing private JSON, never public media."""
    if not data:
        return None
    try:
        content = base64.b64decode(data["data"], validate=True)
        if len(content) > 1024 * 1024 or not content:
            raise ValueError
        kind = data.get("type")
        if kind == "application/pdf":
            if not content.startswith(b"%PDF-"):
                raise ValueError
        elif kind in PRIVATE_ATTACHMENT_TYPES[1:]:
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in ("PNG", "JPEG", "WEBP"):
                    raise ValueError
                image.verify()
        else:
            raise ValueError
        name = str(data.get("name", "attachment")).replace("\\", "/").split("/")[-1][:150]
        if any(ord(c) < 32 for c in name):
            raise ValueError
        return {"name": name, "type": kind, "data": base64.b64encode(content).decode("ascii")}
    except (KeyError, TypeError, ValueError, OSError, Image.DecompressionBombError):
        raise ValidationError("Use a valid PNG, JPEG, WebP or PDF attachment up to 1 MB.")
