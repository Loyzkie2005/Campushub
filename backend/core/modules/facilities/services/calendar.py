"""Read-only calendar projection of existing bookings and structured schedules."""
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from api.models import Booking, Facility, Room
from .booking_workflow import paid_summary, reservation_end, status_label
from .catalog import service_resources_q
from .schedules import SCHEDULE_TYPES, metadata, schedule_days

EVENT_TYPES = {"reservation", *SCHEDULE_TYPES, "blocked", "assessment"}


def calendar_facilities():
    return Facility.objects.filter(is_archived=False).exclude(availability_status=Facility.STATUS_INACTIVE).exclude(
        service_resources_q()).order_by("facility_name")


def calendar_events(first, last, facility_id="", event_type="all", now=None):
    """Expand only the requested dates; rooms/payments are loaded in batches."""
    from api.views import _serialize_booking_event
    now = now or timezone.localtime()
    rows = Booking.objects.filter(
        Q(booking_date__range=(first, last)) |
        Q(check_in_date__lte=last, check_out_date__gt=first) |
        Q(booking_date__lte=last, mobile_request__details__source="schedule",
          mobile_request__details__schedule__until__gte=first.isoformat())
    ).exclude(facility__isnull=True).exclude(service_resources_q("facility__")).exclude(
        status__in=(Booking.STATUS_CANCELLED, Booking.STATUS_REJECTED)
    ).select_related("facility", "user", "mobile_request").prefetch_related("payments")
    if facility_id:
        rows = rows.filter(facility_id=facility_id)
    records = list(rows.order_by("booking_date", "start_time", "pk"))
    room_ids = {row.room_id for row in records if row.room_id}
    rooms = {str(pk): (name, str(facility)) for pk, name, facility in
             Room.objects.filter(pk__in=room_ids).values_list("pk", "room_name", "facility_id")} if room_ids else {}
    events = []
    for booking in records:
        event = _serialize_booking_event(booking)
        details = metadata(booking)
        config = event["schedule"]
        kind = config.get("type", event["type"])
        kind = {"blocked": "hold", "assessment": "other"}.get(kind, kind)
        if kind not in EVENT_TYPES or event_type not in ("all", kind):
            continue
        block = kind != "reservation"
        if block and booking.status not in (Booking.STATUS_PENDING, Booking.STATUS_APPROVED):
            continue
        if booking.status == Booking.STATUS_COMPLETED:
            end = reservation_end(booking)
            if not end or end > now:
                continue  # Completed reservations are historical, not future holds.
        payment = paid_summary(booking) if not block else None
        room = rooms.get(str(booking.room_id))
        room_name = room[0] if room and room[1] == str(booking.facility_id) else ""
        event.update(type=kind, status_label="Active" if block else status_label(booking, payment),
                     payment_status=payment["payment_status"] if payment else "",
                     room=room_name, room_id=str(booking.room_id or ""),
                     first_date=event["date"], all_day=config.get("all_day") is True)
        if event["all_day"]:
            event["start"] = event["end"] = ""  # Stored block bounds remain unchanged.
        if booking.check_in_date and booking.check_out_date and not block:
            clocks = details.get("workflow_snapshot") or booking.facility.workflow_config or {}
            event["start"] = details.get("check_in_time") or clocks.get("check_in_time", "")
            event["end"] = details.get("check_out_time") or clocks.get("check_out_time", "")
            days = (first + timedelta(days=i) for i in range((last-first).days+1)
                    if booking.check_in_date <= first+timedelta(days=i) < booking.check_out_date)
        elif block:
            days = schedule_days(booking, first, last)
        else:
            days = (booking.booking_date,) if booking.booking_date else ()
        for day in days:
            if first <= day <= last:
                events.append({**event, "date": day.isoformat(), "key": f"{booking.pk}:{day.isoformat()}"})
    return sorted(events, key=lambda event: (event["date"], event["start"], event["id"]))


def calendar_data(first, last, facility_id="", event_type="all", now=None):
    """Visible month plus an independent 30-day upcoming horizon; no writes."""
    now = timezone.localtime(now) if now else timezone.localtime()
    today = now.date()
    upcoming_end = today + timedelta(days=30)
    events = calendar_events(first, last, facility_id, event_type, now)
    candidates = (events if first <= today and last >= upcoming_end else
                  calendar_events(today, upcoming_end, facility_id, event_type, now))
    upcoming, seen = [], set()
    for event in candidates:
        if event["status"] == Booking.STATUS_COMPLETED or not today.isoformat() <= event["date"] <= upcoming_end.isoformat():
            continue
        if event["end_date"]:
            finish = datetime.fromisoformat(event["end_date"] + "T" + (event["end"] or "00:00"))
        else:
            finish = datetime.combine(datetime.fromisoformat(event["date"]).date(),
                                      time.max if event["all_day"] else time.fromisoformat(event["end"] or "00:00"))
        if timezone.make_aware(finish) <= now:
            continue
        identity = event["id"] if event["end_date"] else event["key"]
        if identity not in seen:
            upcoming.append(event)
            seen.add(identity)
        if len(upcoming) == 5:
            break
    return {"events": events, "upcoming": upcoming, "today": today.isoformat(),
            "start": first.isoformat(), "end": last.isoformat(), "upcoming_end": upcoming_end.isoformat()}
