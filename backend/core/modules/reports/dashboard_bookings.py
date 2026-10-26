"""Global booking trends, facility rankings and upcoming reservations."""
from modules.facilities.services.schedules import schedule_blocks_q
from modules.facilities.services.catalog import service_resources_q
from datetime import timedelta

from zoneinfo import ZoneInfo

from django.db.models import Case, Count, DateField, F, Max, Q, TimeField, Value, When
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils import timezone

from api.models import Booking, Facility


def upcoming_reservations(*, today=None, now=None):
    """Return at most five future Approved reservations, independent of reporting dates."""
    from accounts.views import _booking_display_fields
    local_now = timezone.localtime(now or timezone.now(), ZoneInfo("Asia/Manila"))
    today = today or local_now.date()
    stays = Q(check_in_date__gte=today, check_out_date__gt=F("check_in_date"))
    events = Q(check_in_date__isnull=True, check_out_date__isnull=True) & (
        Q(booking_date__gt=today) | (Q(booking_date=today) & (
            Q(start_time__gte=local_now.time()) | Q(start_time__isnull=True)
        ))
    )
    bookings = (Booking.objects.exclude(schedule_blocks_q()).exclude(service_resources_q('facility__')).filter(
        stays | events, status=Booking.STATUS_APPROVED, facility__isnull=False,
    ).select_related("facility", "user").annotate(
        reservation_day=Case(When(check_in_date__isnull=False, then=F("check_in_date")),
                             default=F("booking_date"), output_field=DateField()),
        reservation_time=Case(When(check_in_date__isnull=False, then=Value(None)),
                              default=F("start_time"), output_field=TimeField()),
    ).order_by("reservation_day", F("reservation_time").asc(nulls_first=True), "pk")[:5])
    rows = []
    for booking in bookings:
        if booking.check_in_date:
            start, end = booking.check_in_date, booking.check_out_date
            if start.year != end.year:
                when = f"{start:%b %d, %Y}–{end:%b %d, %Y}"
            elif start.month != end.month:
                when = f"{start:%b %d}–{end:%b %d, %Y}"
            else:
                when = f"{start:%b %d}–{end.day}, {end.year}"
        else:
            when = booking.booking_date.strftime("%b %d, %Y")
            if booking.start_time and booking.end_time:
                start = booking.start_time.strftime("%I:%M %p").lstrip("0")
                end = booking.end_time.strftime("%I:%M %p").lstrip("0")
                when += f" · {start} – {end}"
        rows.append({"id": booking.pk, "facility": booking.facility.facility_name,
                     "requester": _booking_display_fields(booking)[1] or "Not recorded",
                     "url": reverse("admin_booking_details_page", kwargs={"booking_id": booking.pk}),
                     "when": when, "status": booking.status,
                     "status_label": booking.get_status_display()})
    return rows


def most_booked_facilities(period):
    """Rank valid usage in the selected period with one grouped database query."""
    usage_dates = Q(booking_date__range=(period.start, period.end)) | (Q(
        booking_date__isnull=True,
        check_in_date__lte=period.end,
        check_out_date__gt=period.start,
    ) & Q(check_out_date__gt=F("check_in_date")))
    rows = (Booking.objects.exclude(schedule_blocks_q()).exclude(service_resources_q('facility__')).filter(
        usage_dates, facility__isnull=False,
        status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
    ).values("facility_id", "facility__facility_name")
        .annotate(booking_count=Count("pk"), facility_image=Max("facility__image_url"))
        .order_by("-booking_count", "facility__facility_name", "facility_id")[:5])
    return [{"rank": rank, "id": row["facility_id"],
             "name": row["facility__facility_name"], "bookings": row["booking_count"],
             "image_url": Facility(image_url=row["facility_image"]).get_first_image_url()}
            for rank, row in enumerate(rows, 1)]


def build_booking_overview(period, totals, comparison, *, grouping="daily", records=None):
    """Reuse the KPI aggregation; add one grouped query for request trends."""
    grouping = grouping if grouping in {"daily", "weekly", "monthly"} else "daily"
    status_keys = {
        Booking.STATUS_PENDING: "pending", Booking.STATUS_APPROVED: "approved",
        Booking.STATUS_COMPLETED: "completed", Booking.STATUS_REJECTED: "rejected_cancelled",
        Booking.STATUS_CANCELLED: "rejected_cancelled",
    }
    keys = ("approved", "pending", "completed", "rejected_cancelled")
    def bucket_key(day):
        if grouping == "daily":
            return day
        if grouping == "weekly":
            return period.start + timedelta(days=(day - period.start).days // 7 * 7)
        return day.replace(day=1)

    buckets = {}
    for offset in range(period.days):
        day = period.start + timedelta(days=offset)
        buckets.setdefault(bucket_key(day), {"start": day, "end": day, "count": 0, **dict.fromkeys(keys, 0)})["end"] = day
    records = Booking.objects.exclude(schedule_blocks_q()) if records is None else records
    rows = (records.filter(created_at__date__range=(period.start, period.end))
            .order_by().annotate(day=TruncDate("created_at")).values("day", "status")
            .annotate(count=Count("pk")))
    for row in rows:
        if row["status"] not in status_keys:
            raise ValueError("Booking Overview contains an unsupported booking status. Review the booking workflow mapping.")
        bucket = buckets[bucket_key(row["day"])]
        bucket[status_keys[row["status"]]] += row["count"]
        bucket["count"] += row["count"]
    trend = []
    for bucket in buckets.values():
        start, end = bucket["start"], bucket["end"]
        label = start.strftime("%b %d") if grouping != "monthly" else start.strftime("%b %Y")
        if grouping == "weekly" and start != end:
            label += " – " + end.strftime("%b %d")
        trend.append({"label": label, "count": bucket["count"], "total": bucket["count"],
                      **{key: bucket[key] for key in keys},
                      "start_date": start.isoformat(), "end_date": end.isoformat()})
    url = reverse("admin_bookings_page")
    statuses = [
        {"key": "pending", "label": "Pending", "count": totals["period_pending"], "url": f"{url}?status=pending"},
        {"key": "approved", "label": "Approved", "count": totals["period_approved"], "url": f"{url}?status=approved"},
        {"key": "completed", "label": "Completed", "count": totals["period_completed"], "url": f"{url}?status=completed"},
        {"key": "rejected_cancelled", "label": "Rejected / Cancelled", "count": totals["period_rejected_cancelled"], "url": None},
    ]
    return {
        "total": totals["current"], **{item["key"]: item["count"] for item in statuses},
        "cancelled": totals["period_rejected_cancelled"],
        "date_basis": "created_at", "start_date": period.start.isoformat(), "end_date": period.end.isoformat(),
        "grouping": grouping, "statuses": statuses, "trend": trend,
        "chart": {"labels": [item["label"] for item in trend], "values": [item["count"] for item in trend],
                  **{key: [item[key] for item in trend] for key in keys}},
        "comparison": comparison, "view_all_url": url,
    }
