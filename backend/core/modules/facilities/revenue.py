"""Shared, database-backed rules for recorded facility revenue."""
from datetime import timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, TruncDate

from api.models import Booking, FacilityPayment


def valid_facility_payments(date_from=None, date_to=None):
    """Paid positive collections on valid bookings, dated in Philippine time."""
    payments = FacilityPayment.objects.filter(
        payment_status=FacilityPayment.PAYMENT_PAID,
        booking__status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
        booking__facility__isnull=False,
        paid_amount__gt=0,
    ).annotate(revenue_date=TruncDate(
        Coalesce("paid_at", "created_at"), tzinfo=ZoneInfo("Asia/Manila")))
    if date_from:
        payments = payments.filter(revenue_date__gte=date_from)
    if date_to:
        payments = payments.filter(revenue_date__lte=date_to)
    return payments


def facility_revenue_summary(start, end, previous_range=None):
    """One grouped query supplies current totals, daily counts and comparison."""
    previous_start, previous_end = previous_range or (start, end)
    rows = valid_facility_payments(min(start, previous_start), max(end, previous_end))
    rows = rows.order_by().values("booking__facility_id", "revenue_date").annotate(
        revenue=Sum("paid_amount"), transactions=Count("pk"))
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    amounts = dict.fromkeys(days, Decimal("0"))
    counts = dict.fromkeys(days, 0)
    by_facility = {}
    previous = Decimal("0")
    for row in rows:
        day, amount = row["revenue_date"], row["revenue"]
        if previous_range and previous_start <= day <= previous_end:
            previous += amount
        if start <= day <= end:
            amounts[day] += amount
            counts[day] += row["transactions"]
            key = row["booking__facility_id"]
            by_facility[key] = by_facility.get(key, Decimal("0")) + amount
    total = sum(amounts.values(), Decimal("0"))
    return {
        "total": f"{total:.2f}", "previous_total": f"{previous:.2f}",
        "transactions": sum(counts.values()), "by_facility": by_facility,
        "chart": {
            "labels": [day.strftime("%b %d") for day in days],
            "dates": [day.isoformat() for day in days],
            "tooltip_labels": [day.strftime("%b %d, %Y") for day in days],
            "values": [float(amounts[day]) for day in days],
            "transactions": [counts[day] for day in days],
        },
    }
