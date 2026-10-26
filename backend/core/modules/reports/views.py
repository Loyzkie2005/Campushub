from modules.facilities.services.schedules import schedule_blocks_q
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO, StringIO
import csv
import json
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from accounts.models import User
from accounts.views import dashboard_required, get_notification_context
from modules.marketplace.services.analytics import (
    AnalyticsPeriod,
    _sales_time_series,
    build_marketplace_analytics,
)
from modules.reports.models import GeneratedReport
from modules.reports.reporting import REPORT_GROUPS, REPORT_TITLES, build_report
from modules.reports.dashboard_periods import build_dashboard_data, resolve_dashboard_period
from modules.marketplace.services.bundle_suggestions import (
    can_view_bundle_suggestions, dashboard_bundle_suggestions,
)

CATEGORY_COLORS = ("#1A1851", "#FCB315", "#626781", "#9396ac", "#d5d7e0")
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


def _aware_dashboard_datetime(value):
    """Read legacy timezone-free values using Django's configured default zone."""
    if value is not None and timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_default_timezone())
    return value


def _format_activity_time(dt):
    if not dt:
        return ""
    local = timezone.localtime(_aware_dashboard_datetime(dt))
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


def _revenue_orders(department_id=None, user=None):
    """Completed and paid Cash on Pickup orders counted as marketplace sales."""
    from api.models import MarketplaceOrder

    qs = MarketplaceOrder.objects.filter(
        status=MarketplaceOrder.STATUS_COMPLETED,
        payment_status=MarketplaceOrder.PAYMENT_PAID,
    )
    if department_id:
        qs = qs.filter(product__seller__department_id=department_id)
    if user is not None:
        from accounts.academic import scope_products
        qs = scope_products(qs, user, prefix="product__")
    return qs


def _sales_overview_summary(orders, period, total, count, *, marketplace=False):
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
    summary = {
        "metrics": metrics,
        "has_sales": count > 0,
        "days": period.days,
        "key": getattr(period, "key", "30"),
        "label": getattr(period, "label", "Last 30 Days"),
        "start": period.start,
        "end": period.end,
    }
    if marketplace:
        # Reuse the aggregate above; legacy/shared callers retain their output.
        summary["comparison"] = {"start": previous_start, "end": previous_end, "days": period.days}
        for metric, baseline in zip(metrics, (previous_total, previous_count, previous_average)):
            defined = metric["key"] != "average" or count > 0
            previous_defined = metric["key"] != "average" or previous_count > 0
            value = {"sales": total, "orders": count, "average": average}[metric["key"]]
            percentage = (Decimal(value) - Decimal(baseline)) / Decimal(baseline) * 100 if defined and baseline else None
            metric["comparison"] = {
                "defined": defined,
                "previous": (f"{baseline:,.2f}" if metric["currency"] else f"{baseline:,}") if previous_defined else None,
                "change": f"{percentage:+.1f}%" if percentage else "0.0%" if percentage is not None else None,
                "note": ("No eligible completed and paid orders are available for this average." if not defined else
                         "Previous period value is zero; percentage change is unavailable." if not baseline else ""),
            }
    return summary


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
    colors = ("#1A1851", "#FCB315", "#787878", "#b5b5b5", "#dedede", "#f8fafc")
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
    if raw_days in {"7", "14", "30", "90"}:
        days = int(raw_days)
        start = today - timedelta(days=days - 1)
        return AnalyticsPeriod(str(days), f"Last {days} Days", start, today), str(days), days

    if raw_period in {"today", "1"}:
        return AnalyticsPeriod("today", "Today", today, today), "today", 1
    elif raw_period in {"7", "last_7_days"}:
        return AnalyticsPeriod("7", "Last 7 Days", today - timedelta(days=6), today), "7", 7
    elif raw_period == "14":
        return AnalyticsPeriod("14", "Last 14 Days", today - timedelta(days=13), today), "14", 14
    elif raw_period in {"90", "last_90_days"}:
        return AnalyticsPeriod("90", "Last 90 Days", today - timedelta(days=89), today), "90", 90
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


def _resolve_marketplace_sales_period(request, today):
    """Validate custom input only for Marketplace; keep existing valid presets."""
    key = (request.GET.get("period") or request.GET.get("sales_period") or request.GET.get("date_range") or "").strip().lower()
    legacy_days = (request.GET.get("sales_days") or "").strip()
    if key == "custom" and legacy_days not in {"7", "14", "30", "90"}:
        try:
            # Existing documented dashboard bounds: <=3,661 days, from 1900.
            resolve_dashboard_period({"period": "custom", "date_from": request.GET.get("date_from"),
                                      "date_to": request.GET.get("date_to")}, today=today)
        except ValueError as error:
            period = AnalyticsPeriod("30", "Last 30 Days", today - timedelta(days=29), today)
            return period, "30", 30, str(error)
    period, key, days = _resolve_sales_period(request, today)
    return period, key, days, ""


def _booking_reserved_hours(booking, operating_hours_per_day, *, period_start=None, period_end=None):
    """Return the reserved hours represented by one approved booking."""
    if booking.start_time and booking.end_time:
        start = datetime.combine(booking.booking_date or timezone.localdate(), booking.start_time)
        end = datetime.combine(booking.booking_date or timezone.localdate(), booking.end_time)
        if end <= start:
            end += timedelta(days=1)
        if period_start and period_end:
            start = max(start, datetime.combine(period_start, datetime.min.time()))
            end = min(end, datetime.combine(period_end + timedelta(days=1), datetime.min.time()))
        return max(0.0, (end - start).total_seconds() / 3600)

    if booking.check_in_date and booking.check_out_date:
        start = max(booking.check_in_date, period_start) if period_start else booking.check_in_date
        end = min(booking.check_out_date, period_end + timedelta(days=1)) if period_end else booking.check_out_date
        reserved_days = max(0, (end - start).days)
        return float(reserved_days * operating_hours_per_day)

    return 0.0


def _facility_dashboard_analytics(today, days, *, period_start=None, revenue_previous_range=None):
    from api.models import Booking, Facility
    from modules.facilities.revenue import facility_revenue_summary
    from .dashboard_facility_status import facility_operational_status

    period_start = period_start or today - timedelta(days=days - 1)
    operating_hours = float(
        getattr(settings, "FACILITY_OPERATING_HOURS_PER_DAY", 8)
    )
    facilities = list(Facility.objects.all().order_by("facility_name"))
    facility_ids = [facility.id for facility in facilities]
    period_filter = Q(booking_date__range=(period_start, today)) | Q(
        booking_date__isnull=True,
        check_in_date__lte=today,
        check_out_date__gt=period_start,
    )
    period_bookings = list(
        Booking.objects.exclude(schedule_blocks_q()).filter(period_filter, facility_id__in=facility_ids)
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
        booking_day = booking.booking_date or max(booking.check_in_date, period_start)
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
                booking, operating_hours, period_start=period_start, period_end=today
            )

    revenue = facility_revenue_summary(period_start, today, revenue_previous_range)
    revenue_by_facility = revenue["by_facility"]

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
        "operational_status": facility_operational_status(facilities),
        "facilities": facility_rows,
        "most_booked": most_booked,
        "period_revenue": revenue["total"],
        "revenue_chart": revenue["chart"],
        "revenue_overview": {key: value for key, value in revenue.items() if key != "by_facility"},
        "schedule_conflicts": schedule_conflicts,
    }


@timezone.override("Asia/Manila")
def _marketplace_operational_dashboard_data(request, user):
    """Dedicated marketplace data; all resources use canonical academic boundaries."""
    from api.models import MarketplaceOrder, Product, SellerRequest
    from accounts.academic import scope_products, scope_seller_requests
    from accounts.activity_service import format_activities
    from accounts.models import AccountActivity
    from accounts.support_scope import scope_marketplace_activity
    from modules.marketplace.services.inventory import (
        low_stock_inventory_rows, active_inventory_reservations, get_product_inventory_snapshot,
    )
    from modules.marketplace.services.inventory_monitor import inventory_url
    from modules.marketplace.services.order_access import admin_order_queryset
    from modules.marketplace.services.analytics import valid_sales_queryset
    from .dashboard_marketplace import category_sales_chart, recent_marketplace_orders, sales_by_product_category, top_selling_products

    today = timezone.localdate()
    grouping = (request.GET.get("grouping") or request.GET.get("sales_grouping") or "daily").strip().lower()
    if grouping not in {"daily", "weekly", "monthly"}:
        grouping = "daily"
    period, sales_period_key, sales_days, date_range_error = _resolve_marketplace_sales_period(request, today)
    products = scope_products(Product.objects.filter(is_archived=False), user)
    product_counts = products.aggregate(total=Count("pk"), pending=Count("pk", filter=Q(approval_status=Product.STATUS_PENDING)),
        approved=Count("pk", filter=Q(approval_status=Product.STATUS_APPROVED)),
        rejected=Count("pk", filter=Q(approval_status=Product.STATUS_REJECTED)))
    # Also retains Orders' protection against legacy multi-owner item snapshots.
    orders = admin_order_queryset(user)
    period_orders = orders.filter(created_at__date__gte=period.start, created_at__date__lte=period.end)
    total_orders = period_orders.count()
    revenue_orders = valid_sales_queryset(user)
    period_revenue = revenue_orders.filter(analytics_at__date__gte=period.start, analytics_at__date__lte=period.end)
    revenue = period_revenue.aggregate(total=Sum("total_price"), count=Count("pk"))
    total_sales = revenue["total"] or Decimal("0")
    completed_count = revenue["count"]
    chart = _sales_time_series(period_revenue, period, grouping)
    overview = _sales_overview_summary(revenue_orders, period, total_sales, completed_count, marketplace=True)
    overview["rows"] = [{"label": label, "sales": f"{sales:,.2f}", "orders": count}
                        for label, sales, count in zip(chart.get("tooltip_labels") or chart["labels"], chart["sales"], chart["orders"])]
    pending = [{"id": p.pk, "name": p.name, "seller": _seller_label(p.owner),
                "category": p.category or "Not Assigned", "submitted": _format_activity_time(p.submitted_at),
                "url": reverse("admin_products_page") + f"?status=pending&product_id={p.pk}"}
               for p in products.filter(approval_status=Product.STATUS_PENDING).select_related("seller", "mobile_seller").order_by("-submitted_at", "-pk")[:6]]
    inventory_rows = low_stock_inventory_rows(products, limit=5, today=today, include_out_of_stock=True)
    # The shortlist intentionally loads minimal fields. Resolve all seller labels once.
    alert_products = {p.pk: p for p in products.filter(
        pk__in={row["product"].pk for row in inventory_rows}).select_related(
            "seller", "mobile_seller").prefetch_related("inventory_skus")}
    reservations = {pk: [] for pk in alert_products}
    for reservation in active_inventory_reservations(product_ids=alert_products):
        reservations[reservation["product_id"]].append(reservation)
    snapshots = {pk: get_product_inventory_snapshot(product, reservation_rows=reservations[pk])
                 for pk, product in alert_products.items()}
    def reserved_quantity(row):
        snapshot = snapshots[row["product"].pk]
        if snapshot is None:
            return None  # Unresolvable historical selections must never become a fake zero.
        if row["variant_key"]:
            return next((variant["reserved"] for variant in snapshot["variant_thresholds"]
                         if variant["variant_key"] == row["variant_key"]), None)
        return snapshot["reserved"]
    low_stock = [{"id": row["product"].pk, "name": row["product"].name,
                  "variant_name": row["variant_name"], "seller": _seller_label(alert_products[row["product"].pk].owner),
                  "reserved": reserved_quantity(row),
                  "stock": row["available"], "threshold": row["threshold"], "is_out_of_stock": row["available"] == 0,
                  "url": inventory_url({"view": "inventory", "product_id": row["product"].pk})}
                 for row in inventory_rows]
    top_products = top_selling_products(period_revenue)
    from modules.marketplace.services.product_access import admin_product_queryset
    from django.db.models import Exists, OuterRef
    top_records = {p.pk: p for p in admin_product_queryset(user).filter(
        pk__in=[row["id"] for row in top_products if row["id"]]).select_related("seller", "mobile_seller").annotate(
            has_recorded_seller=Exists(period_revenue.filter(product_id=OuterRef("pk")).exclude(seller_name="")))}
    for row in top_products:
        product = top_records.get(row["id"])
        row["product_url"] = row["product_url"] if product else ""
        if product and not product.has_recorded_seller:
            owner = product.owner
            row["seller_name"] = ((owner.get_full_name() or owner.username).strip() if owner else "") or "Not recorded"
    categories = _dashboard_product_categories(products)
    category_sales = sales_by_product_category(period_revenue)
    sales_by_name = {row["name"]: Decimal(row["sales"].replace(",", "")) for row in category_sales["categories"]}
    shown = {row["name"] for row in categories["categories"] if row["name"] != "Other categories"}
    for row in categories["categories"]:
        amount = (sum((value for key, value in sales_by_name.items() if key not in shown), Decimal("0"))
                  if row["name"] == "Other categories" else sales_by_name.get(row["name"], Decimal("0")))
        row.update(sales=f"{amount:,.2f}", sales_share=round(amount / total_sales * 100, 1) if total_sales else 0)
    applications = scope_seller_requests(SellerRequest.objects.all(), user)
    seller_counts = applications.aggregate(
        approved=Count("pk", filter=Q(status=SellerRequest.STATUS_APPROVED, is_suspended=False)),
        pending=Count("pk", filter=Q(status=SellerRequest.STATUS_PENDING)),
        suspended=Count("pk", filter=Q(status=SellerRequest.STATUS_APPROVED, is_suspended=True)))
    status_counts = dict(orders.values("status").annotate(count=Count("pk")).values_list("status", "count"))
    status_total = sum(status_counts.values())
    from .dashboard_attention import build_attention_required
    attention = build_attention_required(
        today=today, products=products, pending_products=product_counts["pending"],
        pending_sellers=seller_counts["pending"], pending_orders=status_counts.get(MarketplaceOrder.STATUS_PENDING, 0),
        pending_bookings=0, booking_conflicts=0, maintenance_facilities=0, unavailable_facilities=0)
    status_rows = [{"key": key, "label": label, "count": status_counts.get(key, 0),
                    "percent": round(status_counts.get(key, 0) / status_total * 100) if status_total else 0}
                   for key, label in MarketplaceOrder.STATUS_CHOICES]
    # A created-order cohort measures fulfillment, independently of collected sales.
    period_status_counts = dict(period_orders.values("status").annotate(count=Count("pk")).values_list("status", "count"))
    period_status_rows = [{"key": key, "label": label, "count": period_status_counts.get(key, 0)}
                          for key, label in MarketplaceOrder.STATUS_CHOICES]
    completion_rate = round(period_status_counts.get(MarketplaceOrder.STATUS_COMPLETED, 0) / total_orders * 100, 1) if total_orders else None
    show_bundle_suggestions = can_view_bundle_suggestions(user)
    bundle_analysis = dashboard_bundle_suggestions(user) if show_bundle_suggestions else None
    if bundle_analysis and bundle_analysis.get('unsent_count'):
        attention['items'].append({'key': 'unsent_recommendations', 'count': bundle_analysis['unsent_count'],
            'label': 'Unshared Bundle Suggestions', 'action': 'Review Recommendations',
            'url': reverse('bundle_monitor_list'), 'severity': 'attention'})
    scoped_events = scope_marketplace_activity(AccountActivity.objects.all(), user)
    if show_bundle_suggestions and not bundle_analysis['activity']['error']:
        from modules.marketplace.services.bundle_monitoring import activity_events_for
        from django.db import DatabaseError
        try:
            recommendation_event_ids = list(activity_events_for(user).values_list('pk', flat=True)[:5])
        except DatabaseError:
            recommendation_event_ids = []
        scoped_events = AccountActivity.objects.filter(
            Q(pk__in=scoped_events.values('pk')) | Q(pk__in=recommendation_event_ids))
    events = list(scoped_events.order_by("-created_at", "-pk")[:5])
    def event_reference(event, key):
        value = event.metadata.get(key) if isinstance(event.metadata, dict) else None
        text = str(value)
        return int(text) if text.isascii() and text.isdigit() and len(text) < 19 else None
    event_order_ids = set(orders.filter(pk__in=[event_reference(event, "order_id") for event in events
        if event_reference(event, "order_id") is not None]).values_list("pk", flat=True))
    event_product_ids = set(products.filter(pk__in=[event_reference(event, "product_id") for event in events
        if event_reference(event, "product_id") is not None]).values_list("pk", flat=True))
    def activity_link(event):
        order_id = event_reference(event, "order_id")
        product_id = event_reference(event, "product_id")
        if order_id in event_order_ids:
            return reverse("admin_orders_page") + f"?order={order_id}"
        if order_id is None and product_id in event_product_ids and (
            user.has_perm("accounts.can_view_products") or user.has_perm("accounts.can_manage_products")
        ):
            return inventory_url({"product_id": product_id})
        return ""
    activity_details = format_activities(events, scoped=True, include_targets=False)
    def activity_date(dt):
        local = timezone.localtime(dt)
        date = f"{local.strftime('%b')} {local.day}"
        if local.year != today.year:
            date += f", {local.year}"
        return f"{date}, {local.strftime('%I:%M %p').lstrip('0')}"
    activities = [{"message": event.activity, "type": detail["action"],
                   "performed_by": detail["performed_by"]["name"], "date": activity_date(event.created_at),
                   "url": activity_link(event)}
                  for event, detail in zip(events, activity_details)]
    best = top_products[0]["product_name"] if top_products else "\u2014"
    return {"total_products": product_counts["total"], "pending_listings": product_counts["pending"],
            "total_orders": total_orders, "total_sales": f"{total_sales:,.2f}",
            "sales_grouping": grouping, "sales_days": sales_days, "sales_period": period, "date_range_error": date_range_error,
            "sales_period_key": sales_period_key, "today": today,
            "period_sales_sum": f"{total_sales:.2f}", "period_completed_count": completed_count,
            "sales_overview": overview, "product_categories": categories, "category_sales_chart": category_sales_chart(category_sales),
            "sales_chart": {"grouping": grouping, "labels": chart["labels"],
                            "tooltip_labels": chart.get("tooltip_labels", []), "values": chart["sales"],
                            "sales": chart["sales"], "order_values": chart["orders"], "orders": chart["orders"]},
            "recent_orders": recent_marketplace_orders(period_orders, limit=5), "pending_approvals": pending,
            "low_stock_products": low_stock, "top_selling_products": top_products, "best_selling": best,
            "top_categories": categories["categories"], "category_total": categories["total"],
            "dashboard_stats": {"best_selling": best}, "order_status": status_rows,
            "order_status_total": status_total, "period_order_status": period_status_rows,
            "order_completion_rate": completion_rate, "product_approval_summary": product_counts,
            "seller_overview": seller_counts, "activities": activities,
            "attention_required": attention, "show_bundle_suggestions": show_bundle_suggestions,
            "bundle_analysis": bundle_analysis}


def _facilities_operational_dashboard_data(request, user):
    from .dashboard_facilities import facility_admin_dashboard
    return facility_admin_dashboard(request, user)

@dashboard_required
@never_cache
def admin_dashboard_page(request):
    # 1. Marketplace Admin (Account 2023304612) -> Dedicated Template
    if _is_marketplace_admin(request.user):
        marketplace_data = _marketplace_operational_dashboard_data(
            request, request.user
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            if marketplace_data["date_range_error"]:
                return JsonResponse({"error": marketplace_data["date_range_error"]}, status=400)
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
                "bundle_analysis": marketplace_data["bundle_analysis"],
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
                "dashboard_updated_at": timezone.localtime(timezone.now()),
                **get_notification_context(user=request.user),
            },
            status=400 if marketplace_data["date_range_error"] else 200,
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
                    "booking_grouping": facilities_data["booking_grouping"],
                    "booking_period_label": facilities_data["booking_period_label"],
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
                **get_notification_context(user=request.user),
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
    global_dashboard = request.user.is_superuser or (request.user.role or "").strip().lower() == "super admin"
    global_data = None
    if global_dashboard:
        try:
            today = timezone.localdate(timezone=ZoneInfo("Asia/Manila"))
            global_data = build_dashboard_data(request.GET, today=today, legacy=True)
        except ValueError as error:
            return HttpResponse(str(error), status=400)
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

    if global_data:
        meta = global_data["period"]
        sales_period_key = {
            "last_7_days": "7", "last_14_days": "14", "last_30_days": "30",
            "this_month": "month", "this_year": "year",
        }.get(meta["type"], meta["type"])
        sales_period = AnalyticsPeriod(
            sales_period_key, meta["label"],
            date.fromisoformat(meta["start_date"]), date.fromisoformat(meta["end_date"]),
        )
        sales_days = sales_period.days
        facility_days = booking_days = sales_days
    else:
        sales_period, sales_period_key, sales_days = _resolve_sales_period(request, today)
    use_sales_overview = True

    booking_start = today - timedelta(days=booking_days - 1)
    is_marketplace_admin = _is_marketplace_admin(request.user)
    facility_analytics = (
        None
        if is_marketplace_admin
        else (global_data["facilities"] if global_data else _facility_dashboard_analytics(today, facility_days))
    )
    department_id = getattr(request.user, "department_id", None) if is_marketplace_admin else None
    department_name = ""
    if is_marketplace_admin and getattr(request.user, "department", None):
        department_name = request.user.department.name

    from accounts.academic import scope_products, scope_users
    active_products = scope_products(Product.objects.filter(is_archived=False), request.user)
    if department_id:
        active_products = active_products.filter(seller__department_id=department_id)

    revenue_orders = _revenue_orders(department_id=department_id, user=request.user).annotate(
        analytics_at=Coalesce("completed_at", "paid_at", "created_at")
    )

    order_qs = scope_products(MarketplaceOrder.objects.all(), request.user, prefix="product__")
    if department_id:
        order_qs = order_qs.filter(product__seller__department_id=department_id)

    period_revenue_orders = revenue_orders.filter(
        analytics_at__date__gte=sales_period.start,
        analytics_at__date__lte=sales_period.end,
    )
    if global_data:
        kpis = global_data["kpis"]
        total_orders = int(kpis["total_orders"]["value"])
        total_bookings = int(kpis["total_bookings"]["value"])
        total_revenue = Decimal(str(kpis["marketplace_revenue"]["value"]))
        week_revenue = total_revenue
        period_completed_orders = global_data["marketplace"]["completed_orders"]
        sales_overview = global_data["marketplace"]["sales_overview"]
        leader = global_data["marketplace"]["top_selling_product"]
        overview_top_products = [leader] if leader else []
        pending_sellers = global_data["pending_breakdown"]["seller_requests"]
        pending_products = global_data["pending_breakdown"]["product_approvals"]
        pending_bookings = global_data["pending_breakdown"]["facility_bookings"]
        snapshot_stats = {
            key: kpis[key]["value"] for key in
            ("total_users", "active_sellers", "total_products", "total_facilities")
        }
    else:
        total_orders = order_qs.count()
        total_bookings = 0 if is_marketplace_admin else Booking.objects.exclude(schedule_blocks_q()).count()
        total_revenue = revenue_orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0")
        week_revenue = period_revenue_orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0")
        period_completed_orders = period_revenue_orders.count()
        sales_overview = _sales_overview_summary(revenue_orders, sales_period, week_revenue, period_completed_orders)
        overview_top_products = _dashboard_top_products(revenue_orders)
        pending_sellers = 0 if is_marketplace_admin else SellerRequest.objects.filter(status=SellerRequest.STATUS_PENDING).count()
        pending_products = active_products.filter(approval_status=Product.STATUS_PENDING).count()
        pending_bookings = 0 if is_marketplace_admin else Booking.objects.exclude(schedule_blocks_q()).filter(status=Booking.STATUS_PENDING).count()
        snapshot_stats = {
            "total_users": 0 if is_marketplace_admin else User.objects.count(),
            "active_sellers": User.objects.filter(role="Seller", department_id=department_id).count()
            if department_id else (0 if is_marketplace_admin else User.objects.filter(role="Seller").count()),
            "total_products": active_products.count(),
            "total_facilities": 0 if is_marketplace_admin else Facility.objects.count(),
        }
    best_selling = overview_top_products[0] if overview_top_products else None

    low_stock_count = global_data["attention_required"]["low_stock_products"] if global_data else 0
    if not global_data:
        for product in active_products:
            try:
                if get_product_inventory_status(product) == INVENTORY_STATUS_LOW_STOCK:
                    low_stock_count += 1
            except Exception:
                if (product.get_total_stock() if hasattr(product, "get_total_stock") else product.stock) <= low_stock_threshold():
                    low_stock_count += 1

    dashboard_stats = {
        **snapshot_stats,
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

    time_series = global_data["marketplace"]["sales_trend"] if global_data else _sales_time_series(period_revenue_orders, sales_period, sales_grouping)
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
        Booking.objects.exclude(schedule_blocks_q()).filter(created_at__date__gte=booking_start)
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
        if global_data and request.GET.get("period"):
            return JsonResponse(global_data)
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
    if not is_marketplace_admin and not global_dashboard:
        for b in (
            Booking.objects.exclude(schedule_blocks_q()).filter(
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
        "today_bookings": Booking.objects.exclude(schedule_blocks_q()).filter(
            booking_date=today,
            status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED),
        ).count(),
        "pending_payments": (
            0
            if is_marketplace_admin
            else Booking.objects.exclude(schedule_blocks_q()).filter(
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
    ).select_related("user__department").order_by("-created_at")[:4]:
        approval_items.append(
            {
                "type": "seller",
                "id": req.id,
                "title": f"Seller Request: {(req.full_name or '').strip() or 'Applicant'}",
                "subtitle": (
                    f"Department: {req.user.department.name}"
                    if req.user_id and req.user.department_id
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
        for b in Booking.objects.exclude(schedule_blocks_q()).filter(status=Booking.STATUS_PENDING).order_by(
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
    if not global_data:
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

    recent_orders = global_data["operations"]["recent_orders"] if global_data else []
    for order in ([] if global_data else order_qs.order_by("-created_at")[:6]):
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
        for booking in Booking.objects.exclude(schedule_blocks_q()).select_related("facility", "user").order_by(
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

    activities.sort(key=lambda item: _aware_dashboard_datetime(item["sort"]), reverse=True)
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

    show_bundle_suggestions = can_view_bundle_suggestions(request.user)
    return render(
        request,
        "dashboard/pages/admin_dashboard.html",
        {
            "show_bundle_suggestions": show_bundle_suggestions,
            "bundle_analysis": dashboard_bundle_suggestions(request.user, limit=2) if show_bundle_suggestions else None,
            "global_dashboard": global_dashboard,
            "executive": global_data['executive'] if global_data else None,
            "dashboard_period": global_data["period"] if global_data else None,
            "dashboard_kpis": global_data["kpis"] if global_data else None,
            "attention_required": global_data["attention_required"] if global_data else None,
            "dashboard_marketplace": global_data["marketplace"] if global_data else None,
            "services_overview": global_data["services_overview"] if global_data else None,
            "accounts_overview": global_data["accounts_overview"] if global_data else None,
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
            "dashboard_low_stock": global_data["low_stock"] if global_data else None,
            "recent_orders": recent_orders,
            "facility_operations": facility_operations,
            "upcoming_booking_rows": upcoming_booking_rows,
            "has_facilities": dashboard_stats["total_facilities"] > 0,
            "has_bookings": total_bookings > 0,
            "chat_health_url": _chat_health_url(request),
            "dashboard_updated_at": timezone.localtime(timezone.now(), ZoneInfo("Asia/Manila")) if global_dashboard else timezone.localtime(timezone.now()),
            **get_notification_context(user=request.user),
        },
    )


@require_GET
@never_cache
def admin_dashboard_api(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)
    from accounts.views import can_access_dashboard
    if not user.is_active or not can_access_dashboard(user) or not (
        user.is_superuser or (user.role or "").strip().lower() == "super admin"
    ):
        return JsonResponse({"error": "Super Admin access required."}, status=403)
    if request.GET.get("system_status_only") == "1":
        # Independent health data remains usable when dashboard analytics fail.
        from .dashboard_health import build_system_status
        return JsonResponse({"system_status": build_system_status()})
    try:
        return JsonResponse(build_dashboard_data(request.GET))
    except ValueError as error:
        return JsonResponse({"error": str(error)}, status=400)
    except DatabaseError:
        return JsonResponse({"error": "Dashboard data is unavailable. Please retry."}, status=503)


@login_required(login_url="admin_login_page")
def admin_marketplace_analytics_page(request):
    module = request.GET.get('module', 'marketplace')
    if module != 'marketplace':
        from .analytics_sections import render_domain_analytics
        return render_domain_analytics(request, module)
    if not request.user.has_perm('accounts.can_view_marketplace_analytics'):
        raise PermissionDenied
    try:
        analytics = build_marketplace_analytics(request.GET, user=request.user)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    from .analytics_sections import module_links
    from .superadmin_analytics import is_super_analytics, enrich_marketplace
    super_analytics = is_super_analytics(request.user)
    if super_analytics:
        enrich_marketplace(analytics, request.user)
    return render(
        request,
        "reports/pages/admin_marketplace_analytics.html",
        {
            "analytics": analytics,
            "super_analytics": super_analytics,
            "analytics_period": analytics['period'],
            "analytics_module": 'marketplace',
            "analytics_links": module_links(analytics['period']),
            **get_notification_context(user=request.user),
        },
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_view_facility_analytics", raise_exception=True)
def admin_facility_analytics_page(request):
    from .analytics_sections import render_facility_analytics
    return render_facility_analytics(request)


def _report_parameters(request):
    report_type = request.GET.get("report_type", "sales").strip().lower()
    file_format = request.GET.get("format", "csv").strip().lower()
    date_from = parse_date(request.GET.get("date_from", ""))
    date_to = parse_date(request.GET.get("date_to", ""))
    if (request.GET.get("date_from") and date_from is None) or (request.GET.get("date_to") and date_to is None):
        raise ValueError("Enter valid report dates.")
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
    header = [report["title"], report["range"]]
    if report.get("description"):
        header.append(report["description"])
    writer.writerow(header)
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
    if report.get("description"):
        body.extend([Paragraph(report["description"], styles["Normal"]), Spacer(1, 8)])
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
    date_from = date_to = None
    if request.GET.get("report_type"):
        try:
            first_report_type, _, date_from, date_to = _report_parameters(request)
        except ValueError as exc:
            return HttpResponse(str(exc), status=400)
        _require_report_type_permission(request.user, first_report_type)
    initial_report = build_report(first_report_type, date_from, date_to, user=request.user) if first_report_type else None
    return render(
        request,
        "reports/pages/admin_generate_reports.html",
        {
            "initial_report": initial_report,
            "report_groups": report_groups,
            "selected_report_type": first_report_type,
            "report_date_from": date_from,
            "report_date_to": date_to,
            "recent_reports": (GeneratedReport.objects.all() if request.user.is_superuser else GeneratedReport.objects.filter(generated_by=request.user)).select_related("generated_by")[:6],
            **get_notification_context(user=request.user),
        },
    )


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_view_reports", login_url="admin_dashboard_page")
def admin_report_preview(request):
    try:
        report_type, _, date_from, date_to = _report_parameters(request)
        _require_report_type_permission(request.user, report_type)
        return JsonResponse(build_report(report_type, date_from, date_to, user=request.user))
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@login_required(login_url="admin_login_page")
@permission_required("accounts.can_generate_reports", login_url="admin_dashboard_page")
def admin_report_download(request):
    try:
        report_type, file_format, date_from, date_to = _report_parameters(request)
        _require_report_type_permission(request.user, report_type)
        report = build_report(report_type, date_from, date_to, user=request.user)
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
