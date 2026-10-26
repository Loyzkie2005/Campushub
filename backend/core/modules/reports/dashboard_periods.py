"""Global Super Admin dashboard periods and database-backed summaries."""
from calendar import monthrange
from modules.facilities.services.schedules import schedule_blocks_q
from modules.facilities.services.catalog import service_resources_q
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date

from accounts.models import User
from api.models import Booking, Facility, MarketplaceOrder, Product, SellerRequest
from modules.marketplace.services.analytics import AnalyticsPeriod, _sales_time_series, valid_sales_queryset
from .dashboard_attention import build_attention_required, super_admin_created_products
from .dashboard_marketplace import recent_marketplace_orders, sales_by_product_category, top_selling_products
from .dashboard_low_stock import build_low_stock_card
from .dashboard_bookings import most_booked_facilities, upcoming_reservations
from .dashboard_utilization import build_facility_utilization


PERIOD_LABELS = {
    "today": "Today", "last_7_days": "Last 7 Days", "last_30_days": "Last 30 Days",
    "last_90_days": "Last 90 Days",
    "this_month": "This Month", "previous_month": "Previous Month",
    "this_year": "This Year", "custom": "Custom Range",
}


def resolve_dashboard_period(params, today=None, *, legacy=False):
    today = today or timezone.localdate()
    key = (params.get("period") or "last_30_days").strip().lower()
    aliases = {
        "7": "last_7_days",
        "30": "last_30_days",
        "90": "last_90_days",
        "month": "this_month",
        "year": "this_year",
    }
    key = aliases.get(key, key)
    if legacy and not params.get("period") and params.get("sales_days") in {"7", "14", "30"}:
        days = int(params["sales_days"])
        key = f"last_{days}_days"
    elif key not in PERIOD_LABELS:
        raise ValueError("Choose a valid dashboard period.")
    end = today
    if key == "today":
        start = today
    elif key.startswith("last_"):
        days = int(key.split("_")[1])
        start = today - timedelta(days=days - 1)
    elif key == "this_month":
        start = today.replace(day=1)
    elif key == "previous_month":
        end = today.replace(day=1) - timedelta(days=1)
        start = end.replace(day=1)
    elif key == "this_year":
        start = date(today.year, 1, 1)
    else:
        try:
            start = parse_date(params.get("start_date") or params.get("date_from") or "")
            end = parse_date(params.get("end_date") or params.get("date_to") or "")
        except ValueError:
            start = end = None
        if not start or not end:
            raise ValueError("Enter valid start and end dates.")
        if start > end:
            raise ValueError("Start date must be on or before end date.")
        if end > today:
            raise ValueError("End date cannot be in the future.")
        if (end - start).days > 3660 or start.year < 1900:
            raise ValueError("Choose a range of at most 3,661 days, starting in 1900 or later.")
    label = PERIOD_LABELS.get(key, "Last 14 Days")
    period = AnalyticsPeriod(key, label, start, end)
    if key == "this_month":
        previous_month = start - timedelta(days=1)
        previous_start = previous_month.replace(day=1)
        previous_end = previous_month.replace(day=min(end.day, previous_month.day))
        comparison = "same elapsed days of previous month"
    elif key == "this_year":
        previous_start = date(start.year - 1, 1, 1)
        previous_end = date(end.year - 1, end.month, min(end.day, monthrange(end.year - 1, end.month)[1]))
        comparison = "same elapsed period of previous year"
    elif key == "previous_month":
        previous_end = start - timedelta(days=1)
        previous_start = previous_end.replace(day=1)
        comparison = "previous month"
    else:
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=period.days - 1)
        comparison = "yesterday" if key == "today" else f"previous {period.days} days"
    metadata = {
        "type": key, "label": label, "start_date": start.isoformat(), "end_date": end.isoformat(),
        "previous_start_date": previous_start.isoformat(), "previous_end_date": previous_end.isoformat(),
        "comparison_label": comparison,
    }
    return period, metadata


def comparison_metric(value, previous, label):
    value, previous = Decimal(value), Decimal(previous)
    change = ((value - previous) / previous * 100) if previous else None
    direction = "up" if value > previous else "down" if value < previous else "unchanged"
    if change is None and value:
        text = f"↑ New activity vs {label}"
    elif direction == "unchanged":
        text = f"— No change vs {label}"
    else:
        percentage = f"{abs(change):.1f}".rstrip("0").rstrip(".")
        percentage = "<0.1" if percentage == "0" else percentage
        text = f"{'↑' if direction == 'up' else '↓'} {percentage}% vs {label}"
    secondary = "↑ New activity" if change is None and value else text
    if not value and not previous:
        secondary = "— No change"
    return {
        "value": float(value), "previous_value": float(previous),
        "percentage_change": round(float(change), 2) if change is not None else None,
        "direction": direction, "comparison_text": text,
        "trend_state": "new_activity" if change is None and value else direction,
        "semantic_type": "positive" if direction == "up" else "negative" if direction == "down" else "neutral",
        "comparison_label": label, "secondary_text": secondary,
    }


def period_metric(value, previous, label, empty_text):
    metric = comparison_metric(value, previous, label)
    if not value:
        # Retain the actual prior value and percentage in the API while describing
        # this empty period neutrally in the single visible secondary line.
        metric.update(secondary_text=f"— {empty_text}", semantic_type="neutral", trend_state="empty")
    return metric


def descriptive_metric(value, text, *, direction="unchanged", semantic_type="neutral", **details):
    """Snapshot context, without a fabricated performance percentage."""
    return {"value": value, "secondary_text": text, "direction": direction,
            "trend_state": "descriptive", "semantic_type": semantic_type, **details}


def _count_label(value, singular):
    return f"{value} {singular}{'' if value == 1 else 's'}"


@timezone.override("Asia/Manila")
def build_dashboard_data(params, *, today=None, legacy=False):
    # Import presentation helpers lazily to preserve existing domain dashboards.
    from .views import _count_booking_conflicts, _facility_dashboard_analytics

    period, metadata = resolve_dashboard_period(params, today, legacy=legacy)
    previous_range = (metadata["previous_start_date"], metadata["previous_end_date"])
    current_range = (period.start, period.end)
    grouping = params.get("grouping") or params.get("sales_grouping") or "daily"
    if grouping not in {"daily", "weekly", "monthly"}:
        grouping = "daily"
    booking_grouping = params.get("booking_grouping") or "daily"
    if booking_grouping not in {"daily", "weekly", "monthly"}:
        booking_grouping = "daily"
    service_grouping = params.get('service_grouping') or 'daily'
    if service_grouping not in {'daily', 'weekly', 'monthly'}:
        service_grouping = 'daily'
    users = User.objects.aggregate(
        total=Count("pk"), new=Count("pk", filter=Q(date_joined__date__range=current_range)),
        enabled=Count("pk", filter=Q(is_active=True, is_suspended=False)),
    )
    # Seller access is a permission status, including approved student/faculty users.
    sellers = User.objects.filter(is_active=True, is_suspended=False).exclude(
        seller_access_requests__is_suspended=True
    ).filter(
        Q(role__iexact="Seller") | Q(seller_access_requests__status=SellerRequest.STATUS_APPROVED,
                                    seller_access_requests__is_suspended=False)
    ).aggregate(
        total=Count("pk", distinct=True),
        approved_in_period=Count("pk", distinct=True, filter=Q(
            seller_access_requests__status=SellerRequest.STATUS_APPROVED,
            seller_access_requests__reviewed_at__date__range=current_range,
        )),
        with_recorded_approval=Count("pk", distinct=True, filter=Q(
            seller_access_requests__status=SellerRequest.STATUS_APPROVED,
            seller_access_requests__reviewed_at__isnull=False,
        )),
    )
    products = Product.objects.filter(is_archived=False).aggregate(
        total=Count("pk"), new=Count("pk", filter=Q(submitted_at__date__range=current_range)),
        pending=Count("pk", filter=Q(approval_status=Product.STATUS_PENDING)),
        pending_reviews=Count("pk", filter=Q(approval_status=Product.STATUS_PENDING) & ~super_admin_created_products()),
    )
    facilities = Facility.objects.aggregate(
        total=Count("pk"), new=Count("pk", filter=Q(created_at__date__range=current_range)),
        open=Count("pk", filter=Q(availability_status=Facility.STATUS_AVAILABLE)),
        unavailable=Count("pk", filter=Q(availability_status=Facility.STATUS_UNAVAILABLE)),
        maintenance=Count("pk", filter=Q(availability_status=Facility.STATUS_MAINTENANCE)),
        inactive=Count("pk", filter=Q(availability_status=Facility.STATUS_INACTIVE)),
        active_maintenance=Count("pk", filter=Q(is_archived=False, availability_status=Facility.STATUS_MAINTENANCE)),
        active_unavailable=Count("pk", filter=Q(is_archived=False, availability_status=Facility.STATUS_UNAVAILABLE)),
        physical_maintenance=Count("pk", filter=~service_resources_q() & Q(is_archived=False, availability_status=Facility.STATUS_MAINTENANCE)),
        physical_unavailable=Count("pk", filter=~service_resources_q() & Q(is_archived=False, availability_status=Facility.STATUS_UNAVAILABLE)),
        services=Count("pk", filter=service_resources_q() & Q(is_archived=False)),
        open_services=Count("pk", filter=service_resources_q() & Q(is_archived=False, availability_status=Facility.STATUS_AVAILABLE)),
    )
    pending_sellers = SellerRequest.objects.filter(status=SellerRequest.STATUS_PENDING).count()
    bookings = Booking.objects.exclude(schedule_blocks_q()).aggregate(
        current=Count("pk", filter=Q(created_at__date__range=current_range)),
        previous=Count("pk", filter=Q(created_at__date__range=previous_range)),
        pending=Count("pk", filter=Q(status=Booking.STATUS_PENDING)),
        period_pending=Count("pk", filter=Q(created_at__date__range=current_range, status=Booking.STATUS_PENDING)),
        period_approved=Count("pk", filter=Q(created_at__date__range=current_range, status=Booking.STATUS_APPROVED)),
        period_completed=Count("pk", filter=Q(created_at__date__range=current_range, status=Booking.STATUS_COMPLETED)),
        period_rejected_cancelled=Count("pk", filter=Q(created_at__date__range=current_range, status__in=(Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED))),
        pending_services=Count("pk", filter=service_resources_q("facility__") & Q(status=Booking.STATUS_PENDING)),
    )
    orders = MarketplaceOrder.objects.aggregate(
        current=Count("pk", filter=Q(created_at__date__range=current_range)),
        previous=Count("pk", filter=Q(created_at__date__range=previous_range)),
    )
    revenue_orders = valid_sales_queryset()
    sales = revenue_orders.aggregate(
        current=Sum("total_price", filter=Q(analytics_at__date__range=current_range)),
        previous=Sum("total_price", filter=Q(analytics_at__date__range=previous_range)),
        count=Count("pk", filter=Q(analytics_at__date__range=current_range)),
        previous_count=Count("pk", filter=Q(analytics_at__date__range=previous_range)),
    )
    revenue = sales["current"] or Decimal("0")
    previous_revenue = sales["previous"] or Decimal("0")
    average = revenue / sales["count"] if sales["count"] else Decimal("0")
    previous_average = previous_revenue / sales["previous_count"] if sales["previous_count"] else Decimal("0")
    label = metadata["comparison_label"]
    facility_other = facilities["total"] - sum(facilities[key] for key in ("open", "unavailable", "maintenance", "inactive"))
    facility_summary = [f"{facilities['open']} open for booking"]
    for key, description in (("unavailable", "unavailable"), ("maintenance", "under maintenance"), ("inactive", "inactive")):
        if facilities[key]:
            facility_summary.append(f"{facilities[key]} {description}")
    if facility_other:
        facility_summary.append(f"{facility_other} other statuses")
    if not sellers["total"]:
        seller_text = "— No active sellers"
    elif sellers["with_recorded_approval"]:
        seller_text = f"{'+' if sellers['approved_in_period'] else '— '}{_count_label(sellers['approved_in_period'], 'approval')} recorded in selected period"
    else:
        seller_text = "Current active seller access"
    kpis = {
        "total_users": descriptive_metric(users["total"], f"{'+' if users['new'] else '— '}{users['new']} new in selected period", new_in_period=users["new"], direction="up" if users["new"] else "unchanged"),
        "active_sellers": descriptive_metric(sellers["total"], seller_text, approved_in_period=sellers["approved_in_period"], activation_dates_missing=sellers["total"] - sellers["with_recorded_approval"], direction="up" if sellers["approved_in_period"] else "unchanged"),
        "total_products": descriptive_metric(products["total"], f"{'+' if products['new'] else '— '}{products['new']} added in selected period", new_in_period=products["new"], direction="up" if products["new"] else "unchanged"),
        "total_facilities": descriptive_metric(facilities["total"], " · ".join(facility_summary) if facilities["total"] else "No facilities configured", new_in_period=facilities["new"], open=facilities["open"], unavailable=facilities["unavailable"], maintenance=facilities["maintenance"], inactive=facilities["inactive"], other=facility_other, semantic_type="attention" if facilities["unavailable"] or facilities["maintenance"] else "neutral"),
        "pending_approvals": descriptive_metric(products["pending"] + pending_sellers + bookings["pending"], " · ".join((_count_label(products["pending"], "product"), _count_label(pending_sellers, "seller"), _count_label(bookings["pending"], "booking"))) if products["pending"] + pending_sellers + bookings["pending"] else "— No pending approvals", products=products["pending"], sellers=pending_sellers, bookings=bookings["pending"], semantic_type="attention" if products["pending"] + pending_sellers + bookings["pending"] else "neutral"),
        "total_orders": period_metric(orders["current"], orders["previous"], label, "No orders in selected period"),
        "total_bookings": period_metric(bookings["current"], bookings["previous"], label, "No bookings in selected period"),
        "marketplace_revenue": period_metric(revenue, previous_revenue, label, "No completed sales in selected period" if not sales["count"] else "No marketplace revenue in selected period"),
    }
    period_orders = revenue_orders.filter(analytics_at__date__range=current_range)
    chart = _sales_time_series(period_orders, period, grouping)
    chart.update(values=chart["sales"], order_values=chart["orders"])
    metrics = []
    for key, name, value, baseline, currency in (
        ("sales", "Marketplace Sales", revenue, previous_revenue, True),
        ("orders", "Completed Orders", sales["count"], sales["previous_count"], False),
        ("average", "Average Order Value", average, previous_average, True),
    ):
        comparison = comparison_metric(value, baseline, label)
        legacy_change = (f"{comparison['percentage_change']:+.1f}%" if comparison["percentage_change"] else "0.0%") if baseline else ("No previous sales" if value else "No change")
        metrics.append({
            "key": key, "label": name, "value": f"{value:,.2f}" if currency else f"{value:,}",
            "currency": currency, "change": legacy_change,
            "comparison_text": comparison["comparison_text"], "percentage_change": comparison["percentage_change"],
            "semantic_type": comparison["semantic_type"],
        })
    overview = {
        "metrics": metrics, "has_sales": sales["count"] > 0, "days": period.days, "key": period.key,
        "label": period.label, "start": period.start, "end": period.end,
        "rows": [{"label": day, "sales": f"{amount:,.2f}", "orders": count}
                 for day, amount, count in zip(chart.get("tooltip_labels") or chart["labels"], chart["sales"], chart["orders"])],
    }
    top_products = top_selling_products(period_orders)
    leader = top_products[0] if top_products else None
    categories = sales_by_product_category(period_orders)
    facility_analytics = _facility_dashboard_analytics(period.end, period.days, period_start=period.start,
        revenue_previous_range=tuple(parse_date(value) for value in previous_range))
    revenue = facility_analytics["revenue_overview"]
    revenue["comparison"] = comparison_metric(revenue["total"], revenue["previous_total"], metadata["comparison_label"])
    revenue["start_date"], revenue["end_date"] = metadata["start_date"], metadata["end_date"]
    facility_analytics["schedule_conflicts"] = _count_booking_conflicts(
        Booking.objects.exclude(schedule_blocks_q()).filter(
            status__in=(Booking.STATUS_PENDING, Booking.STATUS_APPROVED),
            booking_date__gte=today or timezone.localdate(),
        ).values("facility_id", "booking_date", "start_time", "end_time")
    )
    facility_analytics.update(
        utilization_summary=build_facility_utilization(period),
        most_booked_facility=facility_analytics["most_booked"],
        most_booked_facilities=most_booked_facilities(period),
        upcoming_reservations=upcoming_reservations(today=today),
        facility_revenue=facility_analytics["period_revenue"],
    )
    facility_analytics["utilization"] = facility_analytics["utilization_summary"]["rows"]
    from .dashboard_executive import executive_overview
    executive = executive_overview(period, metadata, grouping=booking_grouping, service_grouping=service_grouping,
        services_current={'active_services': facilities['open_services'], 'pending_current': bookings['pending_services']})
    # Current work queue, independent of the reporting period; reuse the existing aggregates.
    executive['facility_attention'] = {
        'pending': bookings['pending'] - bookings['pending_services'],
        'maintenance': facilities['physical_maintenance'],
        'unavailable': facilities['physical_unavailable'],
    }
    facility_analytics['booking_overview'] = executive['booking_overview']
    kpis['total_bookings'] = period_metric(executive['booking_overview']['total'],
        executive['booking_overview']['comparison']['previous_value'], label, 'No bookings in selected period')
    if bookings['pending_services']:
        # Shared Booking storage does not turn service applications into space reservations.
        kpis['pending_approvals'].update(bookings=bookings['pending'] - bookings['pending_services'],
            services=bookings['pending_services'], secondary_text=' · '.join((
                _count_label(products['pending'], 'product'), _count_label(pending_sellers, 'seller'),
                _count_label(bookings['pending'] - bookings['pending_services'], 'booking'),
                _count_label(bookings['pending_services'], 'service request'))))
    return {
        "period": metadata, "kpis": kpis,
        "executive": executive,
        "services_overview": {"total": facilities["services"], "open": facilities["open_services"],
                              "pending": bookings["pending_services"]},
        "accounts_overview": {"total": users["total"], "enabled": users["enabled"],
                              "restricted": users["total"] - users["enabled"]},
        "operations": {"recent_orders": recent_marketplace_orders(MarketplaceOrder.objects.all(), limit=5)},
        "low_stock": build_low_stock_card(today=today, include_out_of_stock=True),
        "attention_required": build_attention_required(
            today=today or timezone.localdate(), pending_products=products["pending_reviews"],
            pending_sellers=pending_sellers, pending_bookings=bookings["pending"] - bookings['pending_services'],
            pending_services=bookings['pending_services'],
            booking_conflicts=facility_analytics["schedule_conflicts"],
            maintenance_facilities=facilities["active_maintenance"],
            unavailable_facilities=facilities["active_unavailable"],
        ),
        "marketplace": {
            "completed_orders": sales["count"], "average_order_value": float(average),
            "sales_trend": chart, "top_selling_product": leader, "top_products": top_products,
            "product_categories": categories,
            "sales_overview": overview,
        },
        "facilities": facility_analytics,
        "pending_breakdown": {"seller_requests": pending_sellers, "product_approvals": products["pending"],
                              "facility_bookings": bookings["pending"], "facility_requests": 0},
        "grouping": grouping, "last_updated": timezone.localtime(timezone.now()).isoformat(),
    }
