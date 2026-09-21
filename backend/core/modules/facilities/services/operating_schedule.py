"""Weekly operating hours in the existing facility workflow JSON."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError


WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
TIME_PATTERN = r"\d{1,2}(?::\d{2})?\s*(?:AM|PM)?"


def parse_time(value):
    value = str(value).strip().upper().replace(" ", "")
    for pattern in ("%I:%M%p", "%I%p", "%H:%M"):
        try:
            return datetime.strptime(value, pattern).time()
        except ValueError:
            pass
    raise ValidationError("Use a valid start and end time.")


def parse_time_ranges(raw, *, strict=False):
    ranges = []
    for part in re.split(r"[,;|\n]+", str(raw or "")):
        match = re.fullmatch(
            rf"\s*({TIME_PATTERN})\s*(?:-|\u2013|\u2014|to)\s*({TIME_PATTERN})\s*", part, re.I,
        )
        if not match:
            if strict:
                return []
            continue
        try:
            start, end = map(parse_time, match.groups())
        except ValidationError:
            if strict:
                return []
            continue
        if start >= end and strict:
            return []
        if start < end and (start, end) not in ranges:
            ranges.append((start, end))
    return sorted(ranges)


def validate_weekly_hours(value):
    if not isinstance(value, dict) or set(value) != set(WEEKDAYS):
        raise ValidationError("Set an opening and closing time, or Closed, for each day.")
    cleaned = {}
    for day in WEEKDAYS:
        period = value[day]
        if period is None:
            cleaned[day] = None
            continue
        if not isinstance(period, dict) or set(period) != {"open", "close"}:
            raise ValidationError(f"Select opening and closing times for {day.title()}.")
        if any(not re.fullmatch(r"\d{2}:\d{2}", str(period[key])) for key in ("open", "close")):
            raise ValidationError(f"Select valid times for {day.title()}.")
        start, end = parse_time(period["open"]), parse_time(period["close"])
        if start >= end:
            raise ValidationError(f"{day.title()}: closing time must be after opening time.")
        cleaned[day] = {"open": start.strftime("%H:%M"), "close": end.strftime("%H:%M")}
    return cleaned


def weekly_hours(value):
    """Read structured hours or an unambiguous legacy daily/day-range string.

    None means the old text needs an admin review, not that every day is open.
    """
    if isinstance(value, dict):
        try:
            return validate_weekly_hours(value)
        except ValidationError:
            return None
    raw = str(value or "").strip().lower()
    if not raw:
        return None
    # Legacy forms suggested 'Monday-Friday, 8:00 AM-5:00 PM'.
    days = "|".join(WEEKDAYS)
    match = re.fullmatch(
        rf"(?:(daily|every day|weekdays|weekends|(?:{days})(?:\s*[-\u2013\u2014]\s*(?:{days}))?)\s*[,;:]?\s+)?"
        rf"({TIME_PATTERN})\s*[-\u2013\u2014]\s*({TIME_PATTERN})", raw, re.I,
    )
    if not match:
        return None
    selector, opening, closing = match.groups()
    ranges = parse_time_ranges(f"{opening}-{closing}")
    if not ranges:
        return None
    selected = list(WEEKDAYS)
    if selector == "weekdays":
        selected = list(WEEKDAYS[:5])
    elif selector == "weekends":
        selected = list(WEEKDAYS[5:])
    elif selector and selector not in ("daily", "every day"):
        bounds = re.split(r"\s*[-\u2013\u2014]\s*", selector)
        start_index, end_index = WEEKDAYS.index(bounds[0]), WEEKDAYS.index(bounds[-1])
        selected = [WEEKDAYS[index % 7] for index in range(start_index, end_index + (7 if end_index < start_index else 0) + 1)]
    start, end = ranges[0]
    return {day: {"open": start.strftime("%H:%M"), "close": end.strftime("%H:%M")} if day in selected else None for day in WEEKDAYS}


def duration_hours(value):
    """Retain decimal-hour storage while accepting existing '1 hour' records."""
    if value in (None, ""):
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|minutes?|mins?)?", str(value).strip(), re.I)
    if not match:
        raise ValidationError("Select a valid minimum booking duration.")
    try:
        amount = Decimal(match[1])
        if (match[2] or "").lower().startswith("min"):
            amount /= 60
        if not 0 < amount <= 24 or amount * 60 != (amount * 60).to_integral_value():
            raise InvalidOperation
    except InvalidOperation:
        raise ValidationError("Select a duration between 1 minute and 24 hours.")
    return amount


def workflow_for_display(facility):
    workflow = dict(facility.workflow_config or {})
    hours = weekly_hours(workflow.get("operating_hours"))
    if hours is not None:
        workflow["operating_hours"] = hours
    try:
        duration = duration_hours(workflow.get("minimum_booking_duration"))
        if duration is not None:
            workflow["minimum_booking_duration"] = str(duration)
    except ValidationError:
        pass  # The form asks the admin to choose a valid replacement.
    return workflow
