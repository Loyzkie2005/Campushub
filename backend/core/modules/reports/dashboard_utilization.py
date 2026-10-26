"""Capacity-specific usage for the global dashboard; never assume daily capacity."""
from collections import defaultdict
from datetime import timedelta
import logging

from django.db import DatabaseError
from django.db.models import Q

from api.models import Booking, Facility, Room
from modules.facilities.services.mobile_booking import configured_slots
from modules.facilities.services.operating_schedule import parse_time_ranges, weekly_hours
from modules.facilities.services.schedules import BLOCK_PREFIXES, metadata, schedule_days


logger = logging.getLogger(__name__)
VALID_STATUSES = (Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED)
EXCLUDED_STATUSES = {"maintenance", "unavailable", "inactive"}
TYPES = (
    ("covered_court", "Covered Court", "hours"),
    ("function_hall", "Function Hall", "hours"),
    ("hostel", "Hostel", "room-nights"),
    ("food_analysis", "Food Analysis Hub", "services"),
    ("training_kitchen", "Training/Assessment Center", "slots"),
    ("lease_space", "Commercial/Stall Lease", "units"),
)


class CapacityUnavailable(ValueError):
    """The existing records cannot support a reliable denominator or numerator."""


def _union(intervals):
    merged = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _subtract(intervals, blocked):
    result = _union(intervals)
    for start, end in _union(blocked):
        remaining = []
        for left, right in result:
            if end <= left or start >= right:
                remaining.append((left, right))
            else:
                if left < start:
                    remaining.append((left, start))
                if end < right:
                    remaining.append((end, right))
        result = remaining
    return result


def _minutes(value):
    return value.hour * 60 + value.minute + value.second / 60


def _booking_interval(booking):
    if not booking.start_time or not booking.end_time:
        return None
    start, end = _minutes(booking.start_time), _minutes(booking.end_time)
    return (start, end) if end > start else None


def _blocked(booking):
    return metadata(booking).get("source") == "schedule" or (booking.purpose or "").lstrip().lower().startswith(tuple(f"[{kind}]" for kind in BLOCK_PREFIXES))


def _hours_or_slots(facility, bookings, days, *, slots=False):
    if slots and not facility.slots:
        raise CapacityUnavailable("Available assessment slots are not configured.")
    if not isinstance(facility.workflow_config, dict):
        raise CapacityUnavailable("Operating configuration needs review.")
    workflow = facility.workflow_config
    if not facility.slots and not workflow.get("operating_hours"):
        raise CapacityUnavailable("Operating hours are not configured.")
    raw_hours = workflow.get("operating_hours")
    if raw_hours and weekly_hours(raw_hours) is None and not (isinstance(raw_hours, str) and parse_time_ranges(raw_hours, strict=True)):
        raise CapacityUnavailable("Operating schedule needs valid opening and closing times.")
    if facility.slots and not parse_time_ranges(facility.slots, strict=True):
        raise CapacityUnavailable("Available slots need valid start and end times.")
    by_day = defaultdict(list)
    for booking in bookings:
        for day in schedule_days(booking, min(days), max(days)) if _blocked(booking) else [booking.booking_date]:
            by_day[day].append(booking)
    used = capacity = 0
    for day in days:
        periods = [(_minutes(start), _minutes(end)) for start, end in configured_slots(facility, day)]
        blocks = []
        usage = []
        for booking in by_day[day]:
            interval = _booking_interval(booking)
            if _blocked(booking):
                blocks.extend([interval] if interval else periods)
            elif interval:
                usage.append(interval)
        if slots:
            # A slot with any academic/maintenance overlap cannot be offered whole.
            available = [(left, right) for left, right in periods
                         if not any(start < right and end > left for start, end in blocks)]
            capacity += len(available)
            used += sum(any(start < right and end > left for start, end in usage)
                        for left, right in available)
        else:
            available = _subtract(periods, blocks)
            capacity += sum(right - left for left, right in available) / 60
            intersections = [(max(left, start), min(right, end))
                             for left, right in available for start, end in usage]
            used += sum(right - left for left, right in _union(intersections)) / 60
    return used, capacity


def _booking_days(booking, days):
    if booking.check_in_date and booking.check_out_date:
        return {day for day in days if booking.check_in_date <= day < booking.check_out_date}
    if _blocked(booking):
        return set(schedule_days(booking, min(days), max(days)))
    return {booking.booking_date} & set(days) if _blocked(booking) else set()


def _rooms_or_units(facility, bookings, rooms, days, *, lease=False):
    all_ids = {room.id for room in rooms}
    usable_ids = {room.id for room in rooms if room.status in {"available", "occupied", "reserved"}}
    if not rooms and not lease:
        raise CapacityUnavailable("Individual room inventory is not configured.")
    capacity = len(usable_ids) if rooms else (facility.rooms_units or 0)
    if capacity <= 0:
        return 0, 0
    occupied = set()
    blocked = set()
    for booking in bookings:
        nights = _booking_days(booking, days)
        if not nights:
            if not _blocked(booking) and booking.booking_date in days:
                raise CapacityUnavailable("Room/lease dates and unit assignments need review.")
            continue
        if _blocked(booking):
            if rooms and booking.room_id and booking.room_id not in all_ids:
                raise CapacityUnavailable("Maintenance unit assignments need review.")
            if rooms and booking.room_id in all_ids - usable_ids:
                continue
            units = {booking.room_id} if booking.room_id else usable_ids
            if not rooms and not booking.room_id:
                raise CapacityUnavailable("Maintenance unit assignments are not configured.")
            blocked.update((unit, day) for unit in units for day in nights)
            continue
        if booking.room_id in all_ids - usable_ids:
            continue  # A currently unavailable room/unit contributes no capacity or usage.
        if not booking.room_id or (rooms and booking.room_id not in usable_ids):
            raise CapacityUnavailable("Room/lease unit assignments need review.")
        occupied.update((booking.room_id, day) for day in nights)
    if lease:
        # Period-based unit occupancy, rather than changing the requested metric to unit-days.
        blocked_units = {unit for unit, _ in blocked}
        return len({unit for unit, _ in occupied} - blocked_units), max(0, capacity - len(blocked_units))
    valid_blocks = {(unit, day) for unit, day in blocked if unit in usable_ids}
    return len(occupied - valid_blocks), len(usable_ids) * len(days) - len(valid_blocks)


def _display_number(value):
    return f"{value:,.2f}".rstrip("0").rstrip(".") if value % 1 else f"{int(value):,}"


def _snapshot(period):
    days = [period.start + timedelta(days=offset) for offset in range(period.days)]
    facilities = list(Facility.objects.filter(is_archived=False).order_by("facility_name"))
    by_type = defaultdict(list)
    for facility in facilities:
        by_type[facility.facility_type].append(facility)
    facility_ids = [facility.id for facility in facilities]
    bookings = defaultdict(list)
    usage_filter = Q(booking_date__range=(period.start, period.end)) | Q(
        booking_date__lte=period.end, mobile_request__details__source="schedule",
        mobile_request__details__schedule__until__gte=period.start.isoformat()) | Q(
        check_in_date__lte=period.end, check_out_date__gt=period.start)
    for booking in Booking.objects.select_related("mobile_request").filter(usage_filter, facility_id__in=facility_ids, status__in=VALID_STATUSES):
        bookings[booking.facility_id].append(booking)
    rooms = defaultdict(list)
    for room in Room.objects.filter(facility_id__in=[facility.id for facility in facilities
                                                  if facility.facility_type in {"hostel", "lease_space"}]):
        rooms[room.facility_id].append(room)
    rows = []
    for key, name, unit in TYPES:
        configured = by_type[key]
        row = {"key": key, "name": name, "unit": unit, "state": "unavailable", "percentage": None,
               "used": None, "capacity": None, "context": "", "facility_count": len(configured)}
        used = capacity = 0
        reason = "No facility of this type is configured." if not configured else "No available capacity in the selected period."
        try:
            for facility in configured:
                if facility.availability_status in EXCLUDED_STATUSES:
                    continue
                records = bookings[facility.id]
                if key in {"covered_court", "function_hall", "training_kitchen"}:
                    numerator, denominator = _hours_or_slots(facility, records, days, slots=key == "training_kitchen")
                elif key in {"hostel", "lease_space"}:
                    numerator, denominator = _rooms_or_units(facility, records, rooms[facility.id], days, lease=key == "lease_space")
                else:
                    # Facility.capacity is attendance capacity, not laboratory service throughput.
                    raise CapacityUnavailable("Service capacity and usage records are not configured.")
                used += numerator
                capacity += denominator
            if capacity > 0:
                if used > capacity:
                    raise CapacityUnavailable("Recorded usage exceeds configured capacity; review assignments.")
                percentage = round(used / capacity * 100, 1)
                verb = {"hours": "booked", "room-nights": "occupied", "slots": "used", "units": "occupied"}[unit]
                row.update(state="ready", percentage=percentage, used=round(used, 2), capacity=round(capacity, 2),
                           context=f"{_display_number(used)} of {_display_number(capacity)} available {unit} {verb}")
        except CapacityUnavailable as exception:
            reason = str(exception)
        if row["state"] == "unavailable":
            row["context"] = reason
        rows.append(row)
    return {"state": "ready" if facilities else "empty", "rows": rows,
            "has_usage": any(row["state"] == "ready" and row["used"] > 0 for row in rows),
            "start_date": period.start.isoformat(), "end_date": period.end.isoformat(),
            "unclassified_count": sum(len(group) for key, group in by_type.items() if key not in {item[0] for item in TYPES}),
            "message": "No facilities configured yet." if not facilities else ""}


def build_facility_utilization(period):
    """At most three bounded ORM queries; failures remain errors, not zero usage."""
    try:
        return _snapshot(period)
    except DatabaseError:
        logger.exception("Facility utilization records could not be read")
        return {"state": "error", "rows": [], "message": "Unable to load facility utilization."}
