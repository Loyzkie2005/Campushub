from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
import csv
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.views.decorators.cache import never_cache

from accounts.models import User
from accounts.views import dashboard_required, get_notification_context
from modules.marketplace.services.analytics import (
    AnalyticsPeriod,
    _sales_time_series,
    build_marketplace_analytics,
)
from modules.reports.models import GeneratedReport
from modules.reports.reporting import REPORT_GROUPS, REPORT_TITLES, build_report

CATEGORY_COLORS = ("#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#ea580c")
REPORT_GROUP_PERMISSIONS = {
    "Marketplace": "accounts.can_view_marketplace_reports",
    "Facilities": "accounts.can_view_facility_reports",
    "System": "accounts.can_view_users",
}


def _allowed_report_groups(user):
    return {
        group: options
        for group, options in REPORT_GROUPS.items()
        if user.has_perm(REPORT_GROUP_PERMISSIONS[group])
    }


def _require_report_type_permission(user, report_type):
    for group, options in REPORT_GROUPS.items():
        if report_type in options:
            if not user.has_perm(REPORT_GROUP_PERMISSIONS[group]):
                raise PermissionDenied
            return
    raise PermissionDenied


def _format_activity_time(dt):
    if not dt:
        return ""
    local = timezone.localtime(dt)
    today = timezone.localdate()
    if local.date() == today:
        return local.strftime("%I:%M %p").lstrip("0")
    if local.date() == today - timedelta(days=1):
        return f"Yesterday, {local.strftime('%I:%M %p').lstrip('0')}"
    return local.strftime("%b %d, %I:%M %p").lstrip("0")


def _seller_label(user):
    if not user:
        return "Unknown Seller"
    name = (
        getattr(user, "get_full_name", lambda: "")()
        or getattr(user, "username", "")
        or getattr(user, "email", "")
    ).strip()
    return name or "Unknown Seller"


def _product_image_url(product):
    image = getattr(product, "image", None)
    if image and hasattr(image, "url"):
        try:
            return image.url
        except Exception:
            return None
    return None


def _chat_health_url(request) -> str:
    base_url = settings.CHAT_SERVICE_HTTP_URL.rstrip("/")
    host = request.get_host().split(":", 1)[0]
    if host not in {"127.0.0.1", "localhost", "[::1]"}:
        base_url = f"http://{host}:8001"
    return f"{base_url}/health"


def _count_booking_conflicts(slots) -> int:
    grouped = {}
    for slot in slots:
        if not all(
            (
                slot.get("facility_id"),
                slot.get("booking_date"),
                slot.get("start_time"),
                slot.get("end_time"),
            )
        ):
            continue
        key = (slot["facility_id"], slot["booking_date"])
        grouped.setdefault(key, []).append(slot)

    conflicts = 0
    for day_slots in grouped.values():
        ordered = sorted(day_slots, key=lambda row: row["start_time"])
        for index, current in enumerate(ordered):
            for candidate in ordered[index + 1 :]:
                if candidate["start_time"] >= current["end_time"]:
                    break
                if current["start_time"] < candidate["end_time"]:
                    conflicts += 1
    return conflicts


def _is_marketplace_admin(user) -> bool:
    """Department / Marketplace Admin (not Super Admin)."""
    if getattr(user, "is_superuser", False):
        return False
    role = (getattr(user, "role", "") or "").strip().lower()
    return role in {"marketplace admin", "department admin", "admin"}


def _is_facilities_admin(user) -> bool:
    """Facilities Admin (not Super Admin)."""
    if getattr(user, "is_superuser", False):
        return False
    role = (getattr(user, "role", "") or "").strip().lower()
    return role in {"facilities admin", "facility admin"}


def _requested_analytics_days(request, parameter_name):
    try:
        days = int(request.GET.get(parameter_name, 7))
    except (TypeError, ValueError):
        days = 7
    return days if days in {7, 14, 30} else 7


def _revenue_orders(department_id=None):
    """Completed and paid Cash on Pickup orders counted as marketplace sales."""
    from api.models import MarketplaceOrder

    qs = MarketplaceOrder.objects.filter(
        status=MarketplaceOrder.STATUS_COMPLETED,
        payment_status=MarketplaceOrder.PAYMENT_PAID,
    )
    if department_id:
        qs = qs.filter(product__seller__department_id=department_id)
    return qs


def _sales_overview_summary(orders, period, total, count):
    previous_end = period.start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period.days - 1)
    previous = orders.filter(
        analytics_at__date__gte=previous_start,
        analytics_at__date__lte=previous_end,
    ).aggregate(total=Sum("total_price"), count=Count("id"))
    previous_total = previous["total"] or Decimal("0")
    previous_count = previous["count"]
    average = total / count if count else Decimal("0")
    previous_average = previous_total / previous_count if previous_count else Decimal("0")
    metrics = []
    for key, label, value, baseline, currency in (
        ("sales", "Total Sales", total, previous_total, True),
        ("orders", "Completed Orders", count, previous_count, False),
        ("average", "Average Order Value", average, previous_average, True),
    ):
        if baseline:
            delta = (Decimal(value) - Decimal(baseline)) / Decimal(baseline) * 100
            change = f"{delta:+.1f}%" if delta else "0.0%"
        else:
            change = "No previous sales" if value else "No change"
        metrics.append({
            "key": key, "label": label,
            "value": f"{value:,.2f}" if currency else f"{value:,}",
            "currency": currency, "change": change,
        })
    return {
        "metrics": metrics,
        "has_sales": count > 0,
        "days": period.days,
        "key": getattr(period, "key", "30"),
        "label": getattr(period, "label", "Last 30 Days"),
        "start": period.start,
        "end": period.end,
    }


def _dashboard_top_products(orders):
    rows = orders.values("product_name").annotate(
        units_sold=Sum("quantity"), sales_sum=Sum("total_price")
    ).order_by("-units_sold", "product_name")[:5]
    return [
        {"product_name": row["product_name"], "units_sold": row["units_sold"] or 0,
         "sales": f"{(row['sales_sum'] or Decimal('0')):,.2f}"}
        for row in rows
    ]


def _dashboard_product_categories(products):
    rows = list(products.values("category").annotate(count=Count("id")).order_by("-count", "category"))
    total = sum(row["count"] for row in rows)
    categories = [{"name": row["category"] or "Uncategorized", "count": row["count"]} for row in rows[:5]]
    if len(rows) > 5:
        categories.append({"name": "Other categories", "count": sum(row["count"] for row in rows[5:])})
    colors = ("#1A1851", "#FCB316", "#787878", "#b5b5b5", "#dedede", "#f8fafc")
    circumference = 2 * 3.141592653589793 * 50
    offset = 0
    for category, color in zip(categories, colors):
        length = circumference * category["count"] / total
        category.update(color=color, dasharray=f"{length:.2f} {circumference:.2f}", dashoffset=f"{-offset:.2f}")
        offset += length
    return {"categories": categories, "total": total}


def _sales_filter_parameters(request):
    return [
        (key, value)
        for key, values in request.GET.lists()
        if key not in {
            "grouping",
            "sales_grouping",
            "sales_days",
            "period",
            "sales_period",
            "date_range",
            "date_from",
            "date_to",
        }
        for value in values
    ]


def _resolve_sales_period(request, today: date):
    raw_period = (
        request.GET.get("period")
        or request.GET.get("sales_period")
        or request.GET.get("date_range")
        or ""
    ).strip().lower()
    raw_days = (request.GET.get("sales_days") or "").strip()

    # Prioritize explicit sales_days parameter for backwards compatibility (e.g. tests)
    if raw_days in {"7", "14", "30"}:
        days = int(raw_days)
        start = today - timedelta(days=days - 1)
        return AnalyticsPeriod(str(days), f"Last {days} Days", start, today), str(days), days

    if raw_period in {"today", "1"}:
        return AnalyticsPeriod("today", "Today", today, today), "today", 1
    elif raw_period in {"7", "last_7_days"}:
        return AnalyticsPeriod("7", "Last 7 Days", today - timedelta(days=6), today), "7", 7
    elif raw_period == "14":
        return AnalyticsPeriod("14", "Last 14 Days", today - timedelta(days=13), today), "14", 14
    elif raw_period in {"30", "last_30_days"}:
        return AnalyticsPeriod("30", "Last 30 Days", today - timedelta(days=29), today), "30", 30
    elif raw_period in {"month", "this_month"}:
        start = date(today.year, today.month, 1)
        days = (today - start).days + 1
        return AnalyticsPeriod("month", "This Month", start, today), "month", days
    elif raw_period in {"year", "this_year"}:
        start = date(today.year, 1, 1)
        days = (today - start).days + 1
        return AnalyticsPeriod("year", "This Year", start, today), "year", days
    elif raw_period == "custom":
        date_from = parse_date(request.GET.get("date_from") or "")
        date_to = parse_date(request.GET.get("date_to") or "")
        start = date_from or (today - timedelta(days=29))
        end = date_to or today
        if start > end:
            start, end = end, start
        days = (end - start).days + 1
        label = f"{start.strftime('%b %d, %Y')} – {end.strftime('%b %d, %Y')}"
        return AnalyticsPeriod("custom", label, start, end), "custom", days

    # Default to Last 30 Days
    days = 30
    start = today - timedelta(days=days - 1)
    return AnalyticsPeriod("30", "Last 30 Days", start, today), "30", days


def _booking_reserved_hours(booking, operating_hours_per_day):
    """Return the reserved hours represented by one approved booking."""
    if booking.start_time and booking.end_time:
        start = datetime.combine(booking.booking_date or timezone.localdate(), booking.start_time)
        end = datetime.combine(booking.booking_date or timezone.localdate(), booking.end_time)
        if end <= start:
            end += timedelta(days=1)
        return max(0.0, (end - start).total_seconds() / 3600)

    if booking.check_in_date and booking.check_out_date:
        reserved_days = max(1, (booking.check_out_date - booking.check_in_date).days)
        return float(reserved_days * operating_hours_per_day)

    return 0.0


def _facility_dashboard_analytics(today, days):
    from api.models import Booking, Facility, FacilityPayment

    period_start = today - timedelta(days=days - 1)
    operating_hours = float(
        getattr(settings, "FACILITY_OPERATING_HOURS_PER_DAY", 8)
    )
    facilities = list(Facility.objects.all().order_by("facility_name"))
    facility_ids = [facility.id for facility in facilities]
    period_filter = Q(booking_date__range=(period_start, today)) | Q(
        booking_date__isnull=True,
        check_in_date__range=(period_start, today),
    )
    period_bookings = list(
        Booking.objects.filter(period_filter, facility_id__in=facility_ids)
        .select_related("facility")
        .order_by("booking_date", "start_time")
    )

    chart_statuses = {
        "approved": Booking.STATUS_APPROVED,
        "pending": Booking.STATUS_PENDING,
        "completed": Booking.STATUS_COMPLETED,
    }
    daily_status = {
        key: {period_start + timedelta(days=offset): 0 for offset in range(days)}
        for key in (*chart_statuses.keys(), "cancelled")
    }
    status_totals = {key: 0 for key in daily_status}
    active_statuses = {Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED}
    booking_counts = {facility_id: 0 for facility_id in facility_ids}
    booked_hours = {facility_id: 0.0 for facility_id in facility_ids}

    for booking in period_bookings:
        booking_day = booking.booking_date or booking.check_in_date
        status_key = next(
            (key for key, value in chart_statuses.items() if booking.status == value),
            "cancelled" if booking.status in {Booking.STATUS_CANCELLED, Booking.STATUS_REJECTED} else None,
        )
        if status_key and booking_day in daily_status[status_key]:
            daily_status[status_key][booking_day] += 1
            status_totals[status_key] += 1

        if booking.status in active_statuses and booking.facility_id:
            booking_counts[booking.facility_id] += 1
            booked_hours[booking.facility_id] += _booking_reserved_hours(
                booking, operating_hours
            )

    revenue_by_facility = {facility_id: Decimal("0") for facility_id in facility_ids}
    daily_revenue = {
        period_start + timedelta(days=offset): Decimal("0")
        for offset in range(days)
    }
    try:
        paid_payments = (
            FacilityPayment.objects.filter(
                payment_status=FacilityPayment.PAYMENT_PAID,
                booking__facility_id__in=facility_ids,
            )
            .filter(
                Q(paid_at__date__range=(period_start, today))
                | Q(
                    paid_at__isnull=True,
                    created_at__date__range=(period_start, today),
                )
            )
            .select_related("booking")
        )
        for payment in paid_payments:
            facility_id = payment.booking.facility_id
            if facility_id:
                amount = payment.paid_amount or Decimal("0")
                revenue_by_facility[facility_id] += amount
                paid_on = payment.paid_at or payment.created_at
                if paid_on:
                    if timezone.is_aware(paid_on):
                        paid_on = timezone.localtime(paid_on)
                    if paid_on.date() in daily_revenue:
                        daily_revenue[paid_on.date()] += amount
    except Exception:
        for booking in period_bookings:
            if booking.status in active_statuses and booking.facility_id:
                amount = booking.total_amount or Decimal("0")
                revenue_by_facility[booking.facility_id] += amount
                booking_day = booking.booking_date or booking.check_in_date
                if booking_day in daily_revenue:
                    daily_revenue[booking_day] += amount

    capacity_hours = max(1.0, days * operating_hours)
    facility_rows = []
    for facility in facilities:
        hours = booked_hours.get(facility.id, 0.0)
        utilization = min(100, round((hours / capacity_hours) * 100))
        facility_rows.append(
            {
                "id": facility.id,
                "name": facility.facility_name,
                "bookings": booking_counts.get(facility.id, 0),
                "booked_hours": round(hours, 1),
                "util_pct": utilization,
                "revenue": f"{revenue_by_facility.get(facility.id, Decimal('0')):.2f}",
            }
        )

    facility_rows.sort(key=lambda item: (-item["util_pct"], item["name"].lower()))
    most_booked = max(
        facility_rows,
        key=lambda item: (item["bookings"], item["booked_hours"]),
        default=None,
    )
    if most_booked and not most_booked["bookings"]:
        most_booked = None

    availability = {
        "available": 0,
        "occupied": 0,
        "maintenance": 0,
        "blocked": 0,
    }
    for facility in facilities:
        status = (facility.availability_status or Facility.STATUS_AVAILABLE).lower()
        if status == Facility.STATUS_RESERVED:
            availability["blocked"] += 1
        elif status in availability:
            availability[status] += 1

    conflict_slots = [
        {
            "facility_id": booking.facility_id,
            "booking_date": booking.booking_date,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
        }
        for booking in period_bookings
        if booking.status in {Booking.STATUS_PENDING, Booking.STATUS_APPROVED}
    ]
    schedule_conflicts = _count_booking_conflicts(conflict_slots)

    labels = [
        (period_start + timedelta(days=offset)).strftime("%b %d")
        for offset in range(days)
    ]
    return {
        "days": days,
        "operating_hours": int(operating_hours),
        "chart": {
            "labels": labels,
            **{
                key: [daily_status[key][period_start + timedelta(days=offset)] for offset in range(days)]
                for key in daily_status
            },
        },
        "status_totals": status_totals,
        "availability": availability,
        "facilities": facility_rows,
        "most_booked": most_booked,
        "period_revenue": f"{sum(revenue_by_facility.values(), Decimal('0')):.2f}",
        "revenue_chart": {
            "labels": labels,
            "values": [
                float(daily_revenue[period_start + timedelta(days=offset)])
                for offset in range(days)
            ],
        },
        "schedule_conflicts": schedule_conflicts,
    }


def _marketplace_operational_dashboard_data(request, user):
    from api.models import MarketplaceOrder, Product, SellerRequest
    from django.db.models.functions import Coalesce
    from modules.marketplace.services.analytics import AnalyticsPeriod, _sales_time_series

    today = timezone.localdate()
    grouping = (
        request.GET.get("grouping")
        or request.GET.get("sales_grouping")
        or "daily"
    ).strip().lower()
    if grouping not in {"daily", "weekly", "monthly"}:
        grouping = "daily"

    period, sales_period_key, sales_days = _resolve_sales_period(request, today)

    department_id = (
        getattr(user, "department_id", None) if _is_marketplace_admin(user) else None
    )
    active_products_qs = Product.objects.filter(is_archived=False)
    if department_id:
        active_products_qs = active_products_qs.filter(
            seller__department_id=department_id
        )

    total_products = active_products_qs.count()
    pending_listings = active_products_qs.filter(
        approval_status=Product.STATUS_PENDING
    ).count()

    order_qs = MarketplaceOrder.objects.all()
    if department_id:
        order_qs = order_qs.filter(product__seller__department_id=department_id)
    total_orders = order_qs.count()

    completed_orders_qs = _revenue_orders(department_id=department_id).annotate(
        analytics_at=Coalesce("completed_at", "paid_at", "created_at")
    )
    total_sales_sum = (
        completed_orders_qs.aggregate(total=Sum("total_price"))["total"]
        or Decimal("0.00")
    )

    period_completed_orders = completed_orders_qs.filter(
        analytics_at__date__gte=period.start,
        analytics_at__date__lte=period.end,
    )
    period_completed_count = period_completed_orders.count()
    period_sales_sum = (
        period_completed_orders.aggregate(total=Sum("total_price"))["total"]
        or Decimal("0.00")
    )

    time_series = _sales_time_series(period_completed_orders, period, grouping)
    sales_labels = time_series["labels"]
    sales_tooltip_labels = time_series.get("tooltip_labels", [])
    sales_values = time_series["sales"]
    sales_order_values = time_series["orders"]
    sales_overview = _sales_overview_summary(completed_orders_qs, period, period_sales_sum, period_completed_count)
    sales_overview["rows"] = [
        {"label": label, "sales": f"{sales:,.2f}", "orders": orders}
        for label, sales, orders in zip(sales_tooltip_labels or sales_labels, sales_values, sales_order_values)
    ]

    recent_orders = []
    for o in order_qs.select_related("product").order_by("-created_at")[:8]:
        recent_orders.append(
            {
                "id": o.id,
                "code": o.order_code or f"#{o.id}",
                "buyer_name": (o.buyer_name or "").strip() or "—",
                "product_name": o.product_name,
                "quantity": o.quantity,
                "total": f"{o.total_price:.2f}",
                "status": o.get_status_display(),
                "status_key": (o.status or "pending").lower(),
                "payment_status": (o.payment_status or "unpaid").capitalize(),
                "payment_key": (o.payment_status or "unpaid").lower(),
                "date": (
                    timezone.localtime(o.created_at).strftime("%b %d, %Y")
                    if o.created_at
                    else "—"
                ),
            }
        )

    pending_approvals = []
    for p in (
        active_products_qs.filter(approval_status=Product.STATUS_PENDING)
        .select_related("seller")
        .order_by("-submitted_at")[:6]
    ):
        pending_approvals.append(
            {
                "id": p.id,
                "name": p.name,
                "seller": _seller_label(p.seller),
                "category": p.category or "Not Assigned",
                "submitted": (
                    timezone.localtime(p.submitted_at).strftime("%b %d, %Y")
                    if p.submitted_at
                    else "—"
                ),
            }
        )

    low_stock = []
    for p in active_products_qs.select_related("seller")[:100]:
        try:
            stock_left = (
                p.get_total_stock() if hasattr(p, "get_total_stock") else p.stock
            )
        except Exception:
            stock_left = p.stock or 0
        if stock_left <= 5:
            low_stock.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "seller": _seller_label(p.seller),
                    "stock": stock_left,
                    "is_out_of_stock": stock_left == 0,
                }
            )
        if len(low_stock) >= 6:
            break

    top_selling = _dashboard_top_products(completed_orders_qs)
    best_selling = top_selling[0]["product_name"] if top_selling else "—"

    top_categories_raw = list(
        active_products_qs.exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    category_total = sum(row["count"] for row in top_categories_raw) or 0
    top_categories = []
    circumference = 2 * 3.141592653589793 * 50
    offset = 0.0
    for index, row in enumerate(top_categories_raw):
        count = row["count"]
        pct = (count / category_total) if category_total else 0
        length = circumference * pct
        color = CATEGORY_COLORS[index % len(CATEGORY_COLORS)]
        top_categories.append(
            {
                "name": row["category"],
                "category": row["category"],
                "count": count,
                "percentage": round(pct * 100),
                "color": color,
                "dasharray": f"{length:.2f} {circumference:.2f}",
                "dashoffset": f"{-offset:.2f}",
            }
        )
        offset += length

    seller_users = User.objects.filter(role="Seller")
    seller_requests = SellerRequest.objects.all()
    if department_id:
        seller_users = seller_users.filter(department_id=department_id)
        seller_requests = seller_requests.filter(user__department_id=department_id)

    order_status = {
        "pending": order_qs.filter(status=MarketplaceOrder.STATUS_PENDING).count(),
        "processing": order_qs.filter(
            status=MarketplaceOrder.STATUS_PROCESSING
        ).count(),
        "ready": order_qs.filter(
            status=MarketplaceOrder.STATUS_READY_FOR_PICKUP
        ).count(),
        "completed": order_qs.filter(
            status=MarketplaceOrder.STATUS_COMPLETED
        ).count(),
        "cancelled": order_qs.filter(
            status=MarketplaceOrder.STATUS_CANCELLED
        ).count(),
    }
    order_status_rows = [
        {"key": key, "label": label, "count": order_status[key],
         "percent": round(order_status[key] / total_orders * 100) if total_orders else 0}
        for key, label in (
            ("pending", "Pending"), ("processing", "Processing"),
            ("ready", "Ready for Pickup"), ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        )
    ]

    seller_summary = {
        "active": seller_users.filter(is_active=True, is_suspended=False).count(),
        "pending": seller_requests.filter(status=SellerRequest.STATUS_PENDING).count(),
        "suspended": seller_users.filter(is_suspended=True).count(),
    }

    return {
        "total_products": total_products,
        "pending_listings": pending_listings,
        "total_orders": total_orders,
        "total_sales": f"{total_sales_sum:.2f}",
        "sales_grouping": grouping,
        "sales_days": sales_days,
        "sales_period": period,
        "sales_period_key": sales_period_key,
        "today": today,
        "period_sales_sum": f"{period_sales_sum:.2f}",
        "period_completed_count": period_completed_count,
        "sales_overview": sales_overview,
        "product_categories": _dashboard_product_categories(active_products_qs),
        "sales_chart": {
            "grouping": grouping,
            "labels": sales_labels,
            "tooltip_labels": sales_tooltip_labels,
            "values": sales_values,
            "sales": sales_values,
            "order_values": sales_order_values,
            "orders": sales_order_values,
        },
        "recent_orders": recent_orders,
        "pending_approvals": pending_approvals,
        "low_stock_products": low_stock,
        "top_selling_products": top_selling,
        "best_selling": best_selling,
        "top_categories": top_categories,
        "category_total": category_total,
        "dashboard_stats": {
            "best_selling": best_selling,
        },
        "order_status": order_status_rows,
        "seller_overview": seller_summary,
    }


def _facilities_operational_dashboard_data(request, user):
    from api.models import Booking, Facility, FacilityPayment

    today = timezone.localdate()
    try:
        booking_days = int(request.GET.get("booking_days", 7))
    except (TypeError, ValueError):
        booking_days = 7
    if booking_days not in {7, 14, 30}:
        booking_days = 7

    all_facilities_qs = Facility.objects.all()
    total_facilities = all_facilities_qs.count()
    pending_bookings_qs = Booking.objects.filter(status=Booking.STATUS_PENDING)
    pending_bookings_count = pending_bookings_qs.count()

    upcoming_reservations_qs = (
        Booking.objects.filter(
            status=Booking.STATUS_APPROVED,
            booking_date__gte=today,
        )
        .select_related("facility", "user")
        .order_by("booking_date", "start_time")
    )
    upcoming_count = upcoming_reservations_qs.count()
    maintenance_count = all_facilities_qs.filter(
        availability_status=Facility.STATUS_MAINTENANCE
    ).count()
    bookings_today = Booking.objects.filter(
        booking_date=today,
        status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
    ).count()

    booking_start = today - timedelta(days=booking_days - 1)
    booking_daily = (
        Booking.objects.filter(created_at__date__gte=booking_start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    daily_booking_map = {row["day"]: int(row["total"] or 0) for row in booking_daily}

    booking_labels = []
    booking_values = []
    for offset in range(booking_days):
        day = booking_start + timedelta(days=offset)
        booking_labels.append(day.strftime("%b %d"))
        booking_values.append(daily_booking_map.get(day, 0))
    period_bookings_sum = sum(booking_values)

    upcoming_list = []
    for b in upcoming_reservations_qs[:6]:
        time_label = "Time not set"
        if b.start_time and b.end_time:
            time_label = (
                f"{b.start_time.strftime('%I:%M %p').lstrip('0')} - "
                f"{b.end_time.strftime('%I:%M %p').lstrip('0')}"
            )
        upcoming_list.append(
            {
                "id": b.id,
                "facility_name": (
                    b.facility.facility_name if b.facility else "Facility"
                ),
                "requester": _seller_label(b.user),
                "date": (
                    b.booking_date.strftime("%b %d, %Y") if b.booking_date else "—"
                ),
                "time": time_label,
                "status": b.get_status_display(),
                "status_key": (b.status or "pending").lower(),
            }
        )

    pending_requests = []
    for b in (
        pending_bookings_qs.select_related("facility", "user")
        .order_by("-created_at")[:6]
    ):
        pending_requests.append(
            {
                "id": b.id,
                "requester": _seller_label(b.user),
                "facility_name": (
                    b.facility.facility_name if b.facility else "Facility"
                ),
                "requested_date": (
                    b.booking_date.strftime("%b %d, %Y") if b.booking_date else "—"
                ),
                "purpose": b.purpose or "—",
                "submitted": (
                    timezone.localtime(b.created_at).strftime("%b %d, %Y")
                    if b.created_at
                    else "—"
                ),
            }
        )

    facility_list = [
        {
            "id": f.id,
            "name": f.facility_name,
            "type": (
                f.get_facility_type_display()
                if hasattr(f, "get_facility_type_display")
                else f.facility_type
            ),
            "status": (
                f.get_availability_status_display()
                if hasattr(f, "get_availability_status_display")
                else f.availability_status
            ),
            "status_key": (f.availability_status or "available").lower(),
        }
        for f in all_facilities_qs[:8]
    ]

    conflict_slots = Booking.objects.filter(
        status__in=(Booking.STATUS_PENDING, Booking.STATUS_APPROVED),
        booking_date__gte=today,
        facility_id__isnull=False,
    ).values("id", "facility_id", "booking_date", "start_time", "end_time")
    conflicts = _count_booking_conflicts(conflict_slots)

    schedule_overview = {
        "bookings_today": bookings_today,
        "detected_conflicts": conflicts,
        "maintenance_count": maintenance_count,
        "unavailable_count": all_facilities_qs.filter(
            availability_status=Facility.STATUS_UNAVAILABLE
        ).count(),
    }

    payment_stats = {
        "total_collected": "0.00",
        "pending_payments": 0,
        "recent_receipts": [],
    }
    try:
        paid_payments_qs = FacilityPayment.objects.filter(
            payment_status=FacilityPayment.PAYMENT_PAID
        )
        total_collected = (
            paid_payments_qs.aggregate(total=Sum("paid_amount"))["total"]
            or Decimal("0.00")
        )
        payment_stats["total_collected"] = f"{total_collected:.2f}"

        recorded_booking_ids = (
            paid_payments_qs.filter(official_receipt_no__isnull=False)
            .exclude(official_receipt_no="")
            .values_list("booking_id", flat=True)
        )
        payment_stats["pending_payments"] = (
            Booking.objects.filter(
                status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
                total_amount__gt=0,
            )
            .exclude(id__in=recorded_booking_ids)
            .count()
        )
        for fp in paid_payments_qs.select_related(
            "booking", "booking__facility"
        ).order_by("-paid_at", "-created_at")[:5]:
            payment_stats["recent_receipts"].append(
                {
                    "id": fp.id,
                    "or_number": fp.official_receipt_no or "—",
                    "booking_id": fp.booking_id or "—",
                    "facility_name": (
                        fp.booking.facility.facility_name
                        if (fp.booking and fp.booking.facility)
                        else "Facility"
                    ),
                    "amount": f"{fp.paid_amount:.2f}",
                    "date": (
                        timezone.localtime(fp.paid_at or fp.created_at).strftime(
                            "%b %d, %Y"
                        )
                        if (fp.paid_at or fp.created_at)
                        else "—"
                    ),
                }
            )
    except Exception:
        pass

    return {
        "total_facilities": total_facilities,
        "pending_bookings": pending_bookings_count,
        "upcoming_reservations_count": upcoming_count,
        "maintenance_facilities": maintenance_count,
        "booking_days": booking_days,
        "period_bookings_sum": period_bookings_sum,
        "booking_chart": {
            "labels": booking_labels,
            "values": booking_values,
        },
        "upcoming_reservations": upcoming_list,
        "pending_requests": pending_requests,
        "facilities_list": facility_list,
        "schedule_overview": schedule_overview,
        "payment_stats": payment_stats,
    }


@dashboard_required
@never_cache
def admin_dashboard_page(request):
    # 1. Marketplace Admin (Account 2023304612) -> Dedicated Template
    if _is_marketplace_admin(request.user):
        marketplace_data = _marketplace_operational_dashboard_data(
            request, request.user
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "sales_grouping": marketplace_data["sales_grouping"],
                    "sales_days": marketplace_data["sales_days"],
                    "sales_chart": marketplace_data["sales_chart"],
                    "revenue_chart": marketplace_data["sales_chart"],
                    "period_sales_sum": marketplace_data["period_sales_sum"],
                    "sales_overview": marketplace_data["sales_overview"],
                    "period_completed_count": marketplace_data[
                        "period_completed_count"
                    ],
                }
            )
        return render(
            request,
            "marketplace/pages/admin_marketplace_dashboard.html",
            {
                "marketplace": marketplace_data,
                "dashboard_stats": marketplace_data["dashboard_stats"],
                "best_selling": marketplace_data["best_selling"],
                "top_categories": marketplace_data["top_categories"],
                "category_total": marketplace_data["category_total"],
                "sales_overview": marketplace_data["sales_overview"],
                "sales_days": marketplace_data["sales_days"],
                "sales_period": marketplace_data["sales_period"],
                "sales_period_key": marketplace_data["sales_period_key"],
                "today": marketplace_data["today"],
                "sales_grouping": marketplace_data["sales_grouping"],
                "sales_filter_parameters": _sales_filter_parameters(request),
                "overview_top_products": marketplace_data["top_selling_products"],
                "overview_categories": marketplace_data["product_categories"],
                "chat_health_url": _chat_health_url(request),
                "dashboard_updated_at": timezone.localtime(timezone.now()),
                **get_notification_context(),
            },
        )

    # 2. Facilities Admin (Account 2023304610) -> Dedicated Template
    if _is_facilities_admin(request.user):
        facilities_data = _facilities_operational_dashboard_data(
            request, request.user
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "booking_days": facilities_data["booking_days"],
                    "booking_chart": facilities_data["booking_chart"],
                    "period_bookings_sum": facilities_data["period_bookings_sum"],
                }
            )
        return render(
            request,
            "facilities/pages/admin_facilities_dashboard.html",
            {
                "facilities": facilities_data,
                "chat_health_url": _chat_health_url(request),
                "dashboard_updated_at": timezone.localtime(timezone.now()),
                **get_notification_context(),
            },
        )

    # 3. Super Admin & Other Admins -> Original Untouched Dashboard Template
    from api.models import Booking, Facility, FacilityPayment, MarketplaceOrder, Product, SellerRequest
    try:
        from modules.marketplace.services.inventory import (
            INVENTORY_STATUS_LOW_STOCK,
            get_product_inventory_status,
            low_stock_threshold,
        )
    except ImportError:
        from api.inventory import (
            INVENTORY_STATUS_LOW_STOCK,
            get_product_inventory_status,
            low_stock_threshold,
        )

    today = timezone.localdate()
    sales_grouping = (
        request.GET.get("grouping")
        or request.GET.get("sales_grouping")
        or "daily"
    ).strip().lower()
    if sales_grouping not in {"daily", "weekly", "monthly"}:
        sales_grouping = "daily"

    def requested_chart_days(parameter_name, default=7):
        try:
            value = int(request.GET.get(parameter_name, default))
        except (TypeError, ValueError):
            value = default
        return value if value in {7, 14, 30} else default

    booking_days = requested_chart_days("booking_days")
    facility_days = requested_chart_days("facility_days")

    sales_period, sales_period_key, sales_days = _resolve_sales_period(request, today)
    use_sales_overview = True

    booking_start = today - timedelta(days=booking_days - 1)
    is_marketplace_admin = _is_marketplace_admin(request.user)
    facility_analytics = (
        None
        if is_marketplace_admin
        else _facility_dashboard_analytics(today, facility_days)
    )
    department_id = getattr(request.user, "department_id", None) if is_marketplace_admin else None
    department_name = ""
    if is_marketplace_admin and getattr(request.user, "department", None):
        department_name = request.user.department.name

    active_products = Product.objects.filter(is_archived=False)
    if department_id:
        active_products = active_products.filter(seller__department_id=department_id)

    revenue_orders = _revenue_orders(department_id=department_id).annotate(
        analytics_at=Coalesce("completed_at", "paid_at", "created_at")
    )

    order_qs = MarketplaceOrder.objects.all()
    if department_id:
        order_qs = order_qs.filter(product__seller__department_id=department_id)

    total_orders = order_qs.count()
    total_revenue = revenue_orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0")
    period_revenue_orders = revenue_orders.filter(
        analytics_at__date__gte=sales_period.start,
        analytics_at__date__lte=sales_period.end,
    )
    week_revenue = (
        period_revenue_orders.aggregate(total=Sum("total_price"))["total"]
        or Decimal("0")
    )
    period_completed_orders = period_revenue_orders.count()
    sales_overview = _sales_overview_summary(
        revenue_orders, sales_period, week_revenue, period_completed_orders
    )
    total_bookings = 0 if is_marketplace_admin else Booking.objects.count()

    overview_top_products = _dashboard_top_products(revenue_orders)
    best_selling = overview_top_products[0] if overview_top_products else None

    pending_sellers = (
        0
        if is_marketplace_admin
        else SellerRequest.objects.filter(status=SellerRequest.STATUS_PENDING).count()
    )
    pending_products = active_products.filter(approval_status=Product.STATUS_PENDING).count()
    pending_bookings = (
        0
        if is_marketplace_admin
        else Booking.objects.filter(status=Booking.STATUS_PENDING).count()
    )

    low_stock_count = 0
    for product in active_products:
        try:
            if get_product_inventory_status(product) == INVENTORY_STATUS_LOW_STOCK:
                low_stock_count += 1
        except Exception:
            if (product.get_total_stock() if hasattr(product, "get_total_stock") else product.stock) <= low_stock_threshold():
                low_stock_count += 1

    dashboard_stats = {
        "total_users": 0 if is_marketplace_admin else User.objects.count(),
        "active_sellers": (
            User.objects.filter(role="Seller", department_id=department_id).count()
            if department_id
            else (0 if is_marketplace_admin else User.objects.filter(role="Seller").count())
        ),
        "total_products": active_products.count(),
        "total_facilities": 0 if is_marketplace_admin else Facility.objects.count(),
        "total_orders": total_orders,
        "total_bookings": total_bookings,
        "total_revenue": f"{total_revenue:.2f}",
        "week_revenue": f"{week_revenue:.2f}",
        "pending_approvals": pending_sellers + pending_products + pending_bookings,
        "low_stock": low_stock_count,
        "best_selling": best_selling["product_name"] if best_selling else "—",
    }

    pending_breakdown = {
        "seller_requests": pending_sellers,
        "product_approvals": pending_products,
        "facility_requests": 0,
        "facility_bookings": pending_bookings,
    }

    time_series = _sales_time_series(period_revenue_orders, sales_period, sales_grouping)
    revenue_labels = time_series["labels"]
    revenue_tooltip_labels = time_series.get("tooltip_labels", [])
    revenue_values = time_series["sales"]
    revenue_order_values = time_series["orders"]
    if sales_overview is not None:
        sales_overview["rows"] = [
            {"label": label, "sales": f"{sales:,.2f}", "orders": orders}
            for label, sales, orders in zip(
                revenue_tooltip_labels or revenue_labels, revenue_values, revenue_order_values
            )
        ]

    revenue_chart_payload = {
        "grouping": sales_grouping,
        "labels": revenue_labels,
        "tooltip_labels": revenue_tooltip_labels,
        "values": revenue_values,
        "sales": revenue_values,
        "order_values": revenue_order_values,
        "orders": revenue_order_values,
    }

    booking_daily = (
        Booking.objects.filter(created_at__date__gte=booking_start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    booking_map = {row["day"]: int(row["total"] or 0) for row in booking_daily}
    booking_labels = []
    booking_values = []
    for offset in range(booking_days):
        day = booking_start + timedelta(days=offset)
        booking_labels.append(day.strftime("%b %d"))
        booking_values.append(booking_map.get(day, 0))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "sales_grouping": sales_grouping,
                "sales_days": sales_days,
                "booking_days": booking_days,
                "facility_days": facility_days,
                "week_revenue": f"{week_revenue:.2f}",
                "period_completed_orders": period_completed_orders,
                "sales_overview": sales_overview,
                "revenue_chart": revenue_chart_payload,
                "sales_chart": revenue_chart_payload,
                "booking_chart": {
                    "labels": booking_labels,
                    "values": booking_values,
                },
                "facility_analytics": facility_analytics,
            }
        )

    facility_rows = []
    for f in Facility.objects.all().order_by("facility_name")[:6]:
        facility_rows.append(
            {
                "id": f.id,
                "name": f.facility_name,
                "type": (
                    f.get_facility_type_display()
                    if hasattr(f, "get_facility_type_display")
                    else f.facility_type
                ),
                "status": (
                    f.get_availability_status_display()
                    if hasattr(f, "get_availability_status_display")
                    else f.availability_status
                ),
                "status_key": (f.availability_status or "available").lower(),
            }
        )

    upcoming_booking_rows = []
    if not is_marketplace_admin:
        for b in (
            Booking.objects.filter(
                status=Booking.STATUS_APPROVED,
                booking_date__gte=today,
            )
            .select_related("facility", "user")
            .order_by("booking_date", "start_time")[:6]
        ):
            time_label = "Time not set"
            if b.start_time and b.end_time:
                time_label = (
                    f"{b.start_time.strftime('%I:%M %p').lstrip('0')} - "
                    f"{b.end_time.strftime('%I:%M %p').lstrip('0')}"
                )
            upcoming_booking_rows.append(
                {
                    "facility": (
                        b.facility.facility_name if b.facility else "Facility"
                    ),
                    "requester": _seller_label(b.user),
                    "date": (
                        b.booking_date.strftime("%b %d, %Y")
                        if b.booking_date
                        else "—"
                    ),
                    "time": time_label,
                }
            )

    facility_operations = {
        "active_maintenance": Facility.objects.filter(
            availability_status=Facility.STATUS_MAINTENANCE
        ).count(),
        "today_bookings": Booking.objects.filter(
            booking_date=today,
            status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
        ).count(),
        "pending_payments": (
            0
            if is_marketplace_admin
            else Booking.objects.filter(
                status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
                total_amount__gt=0,
            )
            .exclude(
                id__in=(
                    FacilityPayment.objects.filter(
                        payment_status=FacilityPayment.PAYMENT_PAID,
                        official_receipt_no__isnull=False,
                    )
                    .exclude(official_receipt_no="")
                    .values_list("booking_id", flat=True)
                )
            )
            .count()
        ),
    }

    approval_items = []
    for req in SellerRequest.objects.filter(
        status=SellerRequest.STATUS_PENDING
    ).order_by("-created_at")[:4]:
        approval_items.append(
            {
                "type": "seller",
                "id": req.id,
                "title": f"Seller Request: {(req.full_name or '').strip() or 'Applicant'}",
                "subtitle": (
                    f"Department: {req.department.name}"
                    if req.department_id
                    else "Department not set"
                ),
                "time": _format_activity_time(req.created_at),
                "approve_url": f"/admin/sellers/requests/{req.id}/approve/",
            }
        )

    for p in active_products.filter(approval_status=Product.STATUS_PENDING).order_by(
        "-submitted_at"
    )[:4]:
        approval_items.append(
            {
                "type": "product",
                "id": p.id,
                "title": f'Product Listing: "{p.name}"',
                "subtitle": f"by {_seller_label(p.seller)}",
                "time": _format_activity_time(p.submitted_at),
                "approve_url": f"/admin/products/{p.id}/approve/",
            }
        )

    if not is_marketplace_admin:
        for b in Booking.objects.filter(status=Booking.STATUS_PENDING).order_by(
            "-created_at"
        )[:4]:
            facility_name = (
                b.facility.facility_name if b.facility else "Facility"
            )
            approval_items.append(
                {
                    "type": "facility",
                    "id": b.id,
                    "title": f"Facility Booking: {facility_name}",
                    "subtitle": f"by {_seller_label(b.user)}",
                    "time": _format_activity_time(b.created_at),
                    "approve_url": f"/admin/bookings/{b.id}/approve/",
                }
            )

    pending_product_rows = []
    for p in active_products.filter(approval_status=Product.STATUS_PENDING).order_by(
        "-submitted_at"
    )[:6]:
        pending_product_rows.append(
            {
                "id": p.id,
                "name": p.name,
                "seller": _seller_label(p.seller),
                "category": p.category or "Not Assigned",
                "submitted": (
                    timezone.localtime(p.submitted_at).strftime("%b %d, %Y")
                    if p.submitted_at
                    else "—"
                ),
            }
        )

    low_stock_products = []
    for product in active_products:
        try:
            status = get_product_inventory_status(product)
            if status == INVENTORY_STATUS_LOW_STOCK:
                low_stock_products.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "seller": _seller_label(product.seller),
                        "stock": (
                            product.get_total_stock()
                            if hasattr(product, "get_total_stock")
                            else product.stock
                        ),
                    }
                )
        except Exception:
            stock_left = (
                product.get_total_stock()
                if hasattr(product, "get_total_stock")
                else product.stock
            )
            if stock_left <= low_stock_threshold():
                low_stock_products.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "seller": _seller_label(product.seller),
                        "stock": stock_left,
                    }
                )
        if len(low_stock_products) >= 6:
            break

    recent_orders = []
    for order in order_qs.order_by("-created_at")[:6]:
        image = None
        if order.product_id and getattr(order.product, "image", None):
            image = _product_image_url(order.product)
        recent_orders.append(
            {
                "id": order.id,
                "code": order.order_code or f"#{order.id}",
                "buyer_name": (order.buyer_name or "").strip() or "—",
                "product_name": order.product_name,
                "quantity": order.quantity,
                "total": f"{order.total_price:.2f}",
                "status": (order.status or "pending").replace("_", " ").title(),
                "status_key": (order.status or "pending").lower(),
                "payment_status": (
                    order.payment_status or "unpaid"
                ).capitalize(),
                "payment_key": (order.payment_status or "unpaid").lower(),
                "date": (
                    timezone.localtime(order.created_at).strftime("%b %d, %Y")
                    if order.created_at
                    else "—"
                ),
                "image_url": image,
            }
        )

    activities = []
    if not is_marketplace_admin:
        for req in SellerRequest.objects.select_related("user").order_by(
            "-created_at"
        )[:8]:
            name = (req.full_name or "").strip()
            if not name and req.user_id:
                name = _seller_label(req.user)
            activities.append(
                {
                    "type": "seller",
                    "title": "New seller request submitted",
                    "subtitle": name or "Seller request",
                    "time": _format_activity_time(req.created_at),
                    "sort": req.created_at,
                }
            )

    for product in active_products.select_related("seller").order_by(
        "-submitted_at"
    )[:8]:
        seller = _seller_label(product.seller)
        if product.approval_status == Product.STATUS_PENDING:
            activities.append(
                {
                    "type": "product_pending",
                    "title": f'Product "{product.name}" submitted for approval',
                    "subtitle": f"by {seller}",
                    "time": _format_activity_time(product.submitted_at),
                    "sort": product.submitted_at,
                }
            )
        elif product.approval_status == Product.STATUS_APPROVED:
            activities.append(
                {
                    "type": "product",
                    "title": f'New product "{product.name}" added',
                    "subtitle": f"by {seller}",
                    "time": _format_activity_time(
                        product.approved_at or product.submitted_at
                    ),
                    "sort": product.approved_at or product.submitted_at,
                }
            )

    if not is_marketplace_admin:
        for booking in Booking.objects.select_related("facility", "user").order_by(
            "-created_at"
        )[:8]:
            facility_name = (
                booking.facility.facility_name
                if booking.facility
                else "Facility"
            )
            when = ""
            if booking.booking_date:
                when = booking.booking_date.strftime("%b %d, %Y")
                if booking.start_time and booking.end_time:
                    when += (
                        f" • {booking.start_time.strftime('%I:%M %p').lstrip('0')}"
                        f" - {booking.end_time.strftime('%I:%M %p').lstrip('0')}"
                    )
            activities.append(
                {
                    "type": "booking",
                    "title": f"New booking for {facility_name}",
                    "subtitle": when or "Facility booking",
                    "time": _format_activity_time(booking.created_at),
                    "sort": booking.created_at,
                }
            )

    for order in order_qs.order_by("-created_at")[:8]:
        status_label = (order.status or "pending").replace("_", " ").title()
        order_label = order.order_code or f"#{order.id}"
        activities.append(
            {
                "type": "order",
                "title": f"New order {order_label}",
                "subtitle": f"Total: ₱{order.total_price:.2f} · {status_label}",
                "time": _format_activity_time(order.created_at),
                "sort": order.created_at,
            }
        )

    activities.sort(key=lambda item: item["sort"], reverse=True)
    activities = activities[:10]

    top_booked = sorted(
        facility_rows,
        key=lambda item: item["name"].lower(),
    )[:5]

    top_categories_raw = list(
        active_products.exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    category_total = sum(row["count"] for row in top_categories_raw) or 0
    top_categories = []
    circumference = 2 * 3.141592653589793 * 50
    offset = 0.0
    for index, row in enumerate(top_categories_raw):
        count = row["count"]
        pct = (count / category_total) if category_total else 0
        length = circumference * pct
        color = CATEGORY_COLORS[index % len(CATEGORY_COLORS)]
        top_categories.append(
            {
                "name": row["category"],
                "category": row["category"],
                "count": count,
                "percentage": round(pct * 100),
                "color": color,
                "dasharray": f"{length:.2f} {circumference:.2f}",
                "dashoffset": f"{-offset:.2f}",
            }
        )
        offset += length

    return render(
        request,
        "dashboard/pages/admin_dashboard.html",
        {
            "dashboard_stats": dashboard_stats,
            "pending_breakdown": pending_breakdown,
            "is_marketplace_admin": is_marketplace_admin,
            "today": today,
            "sales_grouping": sales_grouping,
            "sales_days": sales_days,
            "sales_period": sales_period,
            "sales_period_key": sales_period_key,
            "sales_overview": sales_overview,
            "sales_filter_parameters": _sales_filter_parameters(request),
            "overview_top_products": overview_top_products,
            "overview_categories": _dashboard_product_categories(active_products),
            "booking_days": booking_days,
            "department_name": department_name,
            "revenue_chart": revenue_chart_payload,
            "sales_chart": revenue_chart_payload,
            "booking_chart": {
                "labels": booking_labels,
                "values": booking_values,
            },
            "facility_booking_chart": (
                facility_analytics["chart"] if facility_analytics else {}
            ),
            "facility_analytics": facility_analytics,
            "facility_operating_hours": (
                facility_analytics["operating_hours"] if facility_analytics else 8
            ),
            "recent_activities": activities,
            "facilities": facility_rows,
            "top_booked": top_booked,
            "top_categories": top_categories,
            "category_total": category_total,
            "pending_product_rows": pending_product_rows,
            "approval_items": approval_items,
            "low_stock_products": low_stock_products,
            "recent_orders": recent_orders,
            "facility_operations": facility_operations,
            "upcoming_booking_rows": upcoming_booking_rows,
            "has_facilities": dashboard_stats["total_facilities"] > 0,
            "has_bookings": total_bookings > 0,
            "chat_health_url": _chat_health_url(request),
            "dashboard_updated_at": timezone.localtime(timezone.now()),
            **get_notification_context(),
        },
    )


@permission_required("accounts.can_view_marketplace_analytics", raise_exception=True)
def admin_marketplace_analytics_page(request):
    analytics = build_marketplace_analytics(request.GET)
    return render(
        request,
        "reports/pages/admin_marketplace_analytics.html",
        {
            "analytics": analytics,
            **get_notification_context(),
        },
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_view_facility_analytics", raise_exception=True)
def admin_facility_analytics_page(request):
    from api.models import Booking, Facility

    today = timezone.localdate()
    facility_days = _requested_analytics_days(request, "facility_days")
    analytics = _facility_dashboard_analytics(today, facility_days)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "facility_days": facility_days,
                "facility_analytics": analytics,
            }
        )

    upcoming_rows = []
    upcoming = (
        Booking.objects.filter(
            status=Booking.STATUS_APPROVED,
            booking_date__gte=today,
        )
        .select_related("facility", "user")
        .order_by("booking_date", "start_time")[:4]
    )
    for booking in upcoming:
        time_label = "Time not set"
        if booking.start_time and booking.end_time:
            time_label = (
                f"{booking.start_time.strftime('%I:%M %p').lstrip('0')} - "
                f"{booking.end_time.strftime('%I:%M %p').lstrip('0')}"
            )
        upcoming_rows.append(
            {
                "facility": (
                    booking.facility.facility_name if booking.facility else "Facility"
                ),
                "requester": _seller_label(booking.user),
                "date": (
                    booking.booking_date.strftime("%b %d, %Y")
                    if booking.booking_date
                    else "—"
                ),
                "time": time_label,
            }
        )
    return render(
        request,
        "reports/pages/admin_facility_analytics.html",
        {
            "facility_days": facility_days,
            "facility_analytics": analytics,
            "facility_booking_chart": analytics["chart"],
            "facility_operating_hours": analytics["operating_hours"],
            "upcoming_booking_rows": upcoming_rows,
            "total_facilities": Facility.objects.count(),
            **get_notification_context(),
        },
    )


def _report_parameters(request):
    report_type = request.GET.get("report_type", "sales").strip().lower()
    file_format = request.GET.get("format", "csv").strip().lower()
    date_from = parse_date(request.GET.get("date_from", ""))
    date_to = parse_date(request.GET.get("date_to", ""))
    if report_type not in REPORT_TITLES:
        raise ValueError("Choose a valid report type.")
    if file_format not in {"csv", "pdf"}:
        raise ValueError("Choose CSV or PDF format.")
    if date_from and date_to and date_from > date_to:
        raise ValueError("The start date cannot be after the end date.")
    return report_type, file_format, date_from, date_to


def _csv_response(report, filename):
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow([report["title"], report["range"]])
    writer.writerow(report["columns"])
    for row in report["rows"]:
        writer.writerow([row.get(column, "") for column in report["columns"]])
    response = HttpResponse(stream.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
    return response


def _pdf_response(report, filename):
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4, landscape  # type: ignore[import-untyped]
    from reportlab.lib.styles import getSampleStyleSheet  # type: ignore[import-untyped]
    from reportlab.lib.units import mm  # type: ignore[import-untyped]
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # type: ignore[import-untyped]

    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=landscape(A4), leftMargin=12 * mm, rightMargin=12 * mm)
    styles = getSampleStyleSheet()
    body: list = [Paragraph(report["title"], styles["Title"]), Paragraph(report["range"], styles["Normal"]), Spacer(1, 8)]
    data = [report["columns"]] + [
        [str(row.get(column, "")) for column in report["columns"]]
        for row in report["rows"]
    ]
    if report["rows"]:
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A1851")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9DEE8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8FB")]),
        ]))
        body.append(table)
    else:
        body.append(Paragraph("No records found for the selected filters.", styles["Normal"]))
    document.build(body)
    response = HttpResponse(stream.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_view_reports", login_url="admin_dashboard_page")
def admin_generate_reports_page(request):
    report_groups = _allowed_report_groups(request.user)
    first_report_type = next(
        (report_type for options in report_groups.values() for report_type in options),
        None,
    )
    initial_report = build_report(first_report_type) if first_report_type else None
    return render(
        request,
        "reports/pages/admin_generate_reports.html",
        {
            "initial_report": initial_report,
            "report_groups": report_groups,
            "recent_reports": GeneratedReport.objects.select_related("generated_by")[:6],
            **get_notification_context(),
        },
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_view_reports", login_url="admin_dashboard_page")
def admin_report_preview(request):
    try:
        report_type, _, date_from, date_to = _report_parameters(request)
        _require_report_type_permission(request.user, report_type)
        return JsonResponse(build_report(report_type, date_from, date_to))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_generate_reports", login_url="admin_dashboard_page")
def admin_report_download(request):
    try:
        report_type, file_format, date_from, date_to = _report_parameters(request)
        _require_report_type_permission(request.user, report_type)
        report = build_report(report_type, date_from, date_to)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    GeneratedReport.objects.create(
        generated_by=request.user,
        report_type=report_type,
        file_format=file_format,
        date_from=date_from,
        date_to=date_to,
        row_count=len(report["rows"]),
    )
    filename = f"campushub-{slugify(report['title'])}-{timezone.localdate().isoformat()}"
    if file_format == "pdf":
        return _pdf_response(report, filename)
    return _csv_response(report, filename)
