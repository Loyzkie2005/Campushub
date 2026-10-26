"""CampusHub Super Admin Analytics Module.

Provides comprehensive, data-driven analytics for:
1. Marketplace
2. Facilities
3. Services
4. Users

All statistics derive from actual PostgreSQL database records.
No fake or fabricated metrics are used.
"""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from accounts.models import Department, ProgramMajor, User
from accounts.views import get_notification_context
from api.models import (
    Booking,
    CampusHubUser,
    Facility,
    MarketplaceOrder,
    Product,
    SellerRequest,
)
from modules.facilities.services.catalog import service_labels, service_resources_q
from modules.facilities.services.schedules import schedule_blocks_q
from modules.marketplace.services.analytics import (
    AnalyticsPeriod,
    _money,
    _money_text,
    build_marketplace_analytics,
    parse_analytics_period,
    valid_sales_queryset,
)
from .dashboard_periods import build_dashboard_data, resolve_dashboard_period
from .superadmin_analytics import is_super_analytics, chart_table, facility_capacity_rows


def analytics_period(request):
    """Resolve the shared analytics date filter across all four tabs."""
    params = request.GET.copy()
    if params.get("date_from") and params.get("date_to") and (not is_super_analytics(getattr(request, "user", None)) or not params.get("period") or params.get("period") == "custom"):
        params.update(
            period="custom",
            start_date=params["date_from"],
            end_date=params["date_to"],
        )
    if not params.get("period"):
        days = params.get("facility_days", "30")
        if days in ("7", "14", "30", "90"):
            today = timezone.localdate()
            params.update(
                period="custom",
                start_date=(today - timedelta(days=int(days) - 1)).isoformat(),
                end_date=today.isoformat(),
            )
        else:
            params["period"] = "30"
    period = parse_analytics_period(params)
    return params, period


def module_links(period):
    """Build tab navigation links preserving the active date filter."""
    dates = {"period": period.key}
    if period.key == "custom":
        dates.update(
            date_from=period.start.isoformat(),
            date_to=period.end.isoformat(),
        )
    return {
        key: reverse("admin_marketplace_analytics_page")
        + "?"
        + urlencode({**dates, "module": key})
        for key in ("marketplace", "facilities", "services", "users")
    }


def _monthly_buckets(start_date: date, end_date: date) -> list[tuple[date, date, str]]:
    """Return chronological monthly boundaries (first_day, last_day, label)."""
    buckets = []
    cursor = start_date.replace(day=1)
    while cursor <= end_date:
        last_day = monthrange(cursor.year, cursor.month)[1]
        bucket_end = cursor.replace(day=last_day)
        label = cursor.strftime("%b %Y")
        buckets.append((cursor, bucket_end, label))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return buckets


def build_facility_tab_analytics(period: AnalyticsPeriod, params: dict, user=None) -> dict:
    """Build data-driven facilities analytics using database-defined physical facilities."""
    today = timezone.localdate()
    super_view = is_super_analytics(user)
    operating_hours = 8  # Standard university facility operating hours per day
    capacity_hours = max(1.0, float(period.days * operating_hours))

    # 1. Non-service physical facilities (Covered Court, Function Hall, Hostel, etc.)
    physical_facilities = list(
        Facility.objects.exclude(service_resources_q())
        .filter(is_archived=False)
        .order_by("facility_name")
    )
    facility_ids = [f.id for f in physical_facilities]

    # 2. Physical bookings in the selected date range
    period_filter = Q(
        booking_date__range=(period.start, period.end)
    ) | Q(
        booking_date__isnull=True,
        check_in_date__lte=period.end,
        **({"check_out_date__gt": period.start} if super_view else {"check_out_date__gte": period.start}),
    )
    all_period_bookings = list(
        Booking.objects.exclude(schedule_blocks_q())
        .exclude(service_resources_q("facility__"))
        .filter(period_filter, facility_id__in=facility_ids)
        .select_related("facility")
        .order_by("booking_date", "start_time")
    )

    # 3. KPI Cards
    total_bookings = len(all_period_bookings)
    approved_bookings_list = [
        b for b in all_period_bookings
        if b.status in {Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED}
    ]
    approved_count = len(approved_bookings_list)
    pending_count = sum(1 for b in all_period_bookings if b.status == Booking.STATUS_PENDING)
    cancelled_rejected_count = sum(
        1 for b in all_period_bookings
        if b.status in {Booking.STATUS_CANCELLED, Booking.STATUS_REJECTED}
    )

    # 4. Main Bar Graph — Bookings by Facility
    facility_approved_counts = {f.id: 0 for f in physical_facilities}
    facility_booked_hours = {f.id: 0.0 for f in physical_facilities}

    for b in approved_bookings_list:
        if b.facility_id in facility_approved_counts:
            facility_approved_counts[b.facility_id] += 1
            if super_view:
                continue  # Verified capacity calculators supply usage below.
            # Calculate hours if start/end times exist
            if b.start_time and b.end_time:
                from datetime import datetime
                t_start = datetime.combine(period.start, b.start_time)
                t_end = datetime.combine(period.start, b.end_time)
                if t_end > t_start:
                    diff_hours = (t_end - t_start).total_seconds() / 3600.0
                    facility_booked_hours[b.facility_id] += diff_hours
            elif b.check_in_date and b.check_out_date:
                # Hotel/Hostel room nights
                nights = max(1, (b.check_out_date - b.check_in_date).days)
                facility_booked_hours[b.facility_id] += nights * operating_hours

    facility_labels = [f.facility_name for f in physical_facilities]
    facility_values = [facility_approved_counts[f.id] for f in physical_facilities]
    facility_tooltips = [
        f"{f.facility_name}: {facility_approved_counts[f.id]} approved booking{'s' if facility_approved_counts[f.id] != 1 else ''}"
        for f in physical_facilities
    ]

    # 5. Booking Status Breakdown
    status_counts = {
        Booking.STATUS_APPROVED: sum(1 for b in all_period_bookings if b.status == Booking.STATUS_APPROVED),
        Booking.STATUS_COMPLETED: sum(1 for b in all_period_bookings if b.status == Booking.STATUS_COMPLETED),
        Booking.STATUS_PENDING: pending_count,
        Booking.STATUS_CANCELLED: sum(1 for b in all_period_bookings if b.status == Booking.STATUS_CANCELLED),
        Booking.STATUS_REJECTED: sum(1 for b in all_period_bookings if b.status == Booking.STATUS_REJECTED),
    }
    status_labels = {
        Booking.STATUS_APPROVED: "Approved",
        Booking.STATUS_COMPLETED: "Completed",
        Booking.STATUS_PENDING: "Pending",
        Booking.STATUS_CANCELLED: "Cancelled",
        Booking.STATUS_REJECTED: "Rejected",
    }
    status_rows = []
    for s_code in (
        Booking.STATUS_APPROVED,
        Booking.STATUS_COMPLETED,
        Booking.STATUS_PENDING,
        Booking.STATUS_CANCELLED,
        Booking.STATUS_REJECTED,
    ):
        cnt = status_counts[s_code]
        pct = round((cnt / total_bookings * 100), 1) if total_bookings else 0.0
        status_rows.append({
            "status": s_code,
            "label": status_labels[s_code],
            "count": cnt,
            "percentage": pct,
        })

    # 6. Monthly Booking Trend
    # For monthly trend, determine window (at least 6 months if period is short, or exact range)
    trend_start = period.start
    if not super_view and period.days < 180:
        # Show past 6 months to give an insightful view
        trend_start = min(period.start, today.replace(day=1) - timedelta(days=150))
    monthly_buckets = _monthly_buckets(trend_start, period.end)

    trend_labels = []
    trend_values = []
    submitted_by_month = {}
    if super_view:
        from django.db.models.functions import TruncMonth
        submitted_by_month = {row['month'].date(): row['count'] for row in Booking.objects.exclude(
            schedule_blocks_q()).exclude(service_resources_q('facility__')).filter(
            facility_id__in=facility_ids, status__in={Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED},
            created_at__date__range=(period.start, period.end)).annotate(month=TruncMonth('created_at'))
            .values('month').annotate(count=Count('pk'))}
    for m_start, m_end, m_label in monthly_buckets:
        m_count = submitted_by_month.get(m_start, 0) if super_view else Booking.objects.exclude(schedule_blocks_q()).exclude(
            service_resources_q("facility__")
        ).filter(
            facility_id__in=facility_ids,
            status__in={Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED},
            created_at__date__range=(m_start, m_end),
        ).count()
        trend_labels.append(m_label)
        trend_values.append(m_count)

    # 7. Most Frequently Booked Facility
    ranked_facilities = []
    verified_capacity = facility_capacity_rows(period, physical_facilities) if super_view else {}
    for f in physical_facilities:
        bookings_cnt = facility_approved_counts[f.id]
        hours_cnt = round(facility_booked_hours[f.id], 1)
        utilization_pct = min(100, round((hours_cnt / capacity_hours) * 100))
        ranked_facilities.append({
            "id": f.id,
            "name": f.facility_name,
            "type": f.get_facility_type_display(),
            "status": f.get_availability_status_display(),
            "bookings": bookings_cnt,
            "booked_hours": hours_cnt,
            "utilization": utilization_pct,
            "percentage": round((bookings_cnt / approved_count * 100), 1) if approved_count else 0.0,
            **verified_capacity.get(f.id, {}),
        })

    ranked_facilities.sort(key=lambda x: (-x["bookings"], -(x["booked_hours"] or 0), x["name"]))
    most_frequent = ranked_facilities[0] if ranked_facilities and ranked_facilities[0]["bookings"] > 0 else None

    return {
        "kpis": {
            "total_bookings": total_bookings,
            "approved_bookings": approved_count,
            "pending_bookings": pending_count,
            "cancelled_rejected_bookings": cancelled_rejected_count,
        },
        "main_chart": {
            "labels": facility_labels,
            "values": facility_values,
            "tooltip_labels": facility_tooltips,
        },
        "monthly_trend": {
            "labels": trend_labels,
            "values": trend_values,
        },
        "status_breakdown": {
            "total": total_bookings,
            "rows": [] if super_view and not total_bookings else status_rows,
        },
        "main_table": chart_table(["Facility", "Approved/completed bookings by booking or stay date"], zip(facility_labels, facility_values)) if super_view else None,
        "trend_table": chart_table(["Month of submission", "Currently approved/completed bookings submitted in selected dates"], zip(trend_labels, trend_values)) if super_view else None,
        "has_bookings": approved_count > 0, "has_trend": any(trend_values),
        "most_frequent": most_frequent,
        "facility_table": ranked_facilities,
    }


def service_request_breakdown(requests_qs, *, limit=None, by_id=False):
    """One grouped projection shared by Services Analytics and the executive chart."""
    fields = ('facility_id', 'facility__facility_name') if by_id else ('facility__facility_name',)
    rows = requests_qs.values(*fields).annotate(
        total=Count('pk'), pending=Count('pk', filter=Q(status=Booking.STATUS_PENDING)),
        approved=Count('pk', filter=Q(status=Booking.STATUS_APPROVED)),
        completed=Count('pk', filter=Q(status=Booking.STATUS_COMPLETED)),
        closed=Count('pk', filter=Q(status__in=(Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED))),
    ).order_by('-total', 'facility__facility_name', *(['facility_id'] if by_id else []))
    return list(rows[:limit] if limit is not None else rows)


def build_services_tab_analytics(period: AnalyticsPeriod, params: dict, user=None) -> dict:
    """Build Services Analytics: Authentic overview of registered services and real request metrics."""
    # Registered services from the database
    service_facilities = list(
        Facility.objects.filter(service_resources_q(), is_archived=False)
        .order_by("facility_name")
    )

    services_list = []
    for f in service_facilities:
        cat_label, req_label = service_labels(f)
        rate_text = f"₱{f.rate:,.2f}"
        if f.price_type:
            rate_text += f" / {f.price_type}"

        is_food_analysis = (
            f.facility_type == Facility.TYPE_FOOD_ANALYSIS
            or "food analysis" in f.facility_name.lower()
        )
        services_list.append({
            "id": f.id,
            "name": f.facility_name,
            "category": cat_label,
            "request_type": req_label,
            "rate": rate_text,
            "location": f.location or "USTP Oroquieta Campus",
            "capacity": f.capacity or "N/A",
            "availability_status": f.availability_status,
            "status_display": f.get_availability_status_display(),
            "description": f.description or "Official institutional university service.",
            "is_food_analysis": is_food_analysis,
        })

    # Service requests in period
    requests_qs = Booking.objects.filter(
        service_resources_q("facility__")
    ).exclude(schedule_blocks_q()).filter(
        created_at__date__range=(period.start, period.end)
    )

    total_requests = requests_qs.count()
    pending_count = requests_qs.filter(status=Booking.STATUS_PENDING).count()
    approved_count = requests_qs.filter(status=Booking.STATUS_APPROVED).count()
    completed_count = requests_qs.filter(status=Booking.STATUS_COMPLETED).count()
    closed_count = requests_qs.filter(
        status__in={Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED}
    ).count()

    # Breakdown by service
    breakdown_rows = service_request_breakdown(requests_qs)

    return {
        "services": services_list,
        "kpis": {
            "registered_services": len(services_list),
            "total_requests": total_requests,
            "pending_requests": pending_count,
            "approved_requests": approved_count,
            "completed_requests": completed_count,
            "closed_requests": closed_count,
        },
        "has_activity": total_requests > 0,
        "breakdown": breakdown_rows,
        "iso_info": {
            "focal_person": "Conmar C. Malmis",
            "office": "USTP Oroquieta Business Enterprise Unit (BEU)",
            "document_code": "DPM-USTP-Oro-BEU-004",
            "procedure_name": "Food Analysis Laboratory Services",
            "job_order_form": "FM-USTP-Oro-BEU-001",
            "soa_form": "FM-USTP-Oro-BEU-002",
            "feedback_form": "FM-USTP-Oro-BEU-Survey",
        },
    }


def build_users_tab_analytics(period: AnalyticsPeriod, params: dict, user=None) -> dict:
    """Build Users Analytics: Account registrations, distribution, and seller privilege stats."""
    today = timezone.localdate()
    super_view = is_super_analytics(user)

    # 1. Account queries
    mobile_qs = CampusHubUser.objects.all()
    admin_qs = User.objects.all()

    total_mobile = mobile_qs.count()
    total_admin = admin_qs.count()
    total_users = total_mobile + total_admin

    # New registrations in period
    new_mobile = mobile_qs.filter(created_at__date__range=(period.start, period.end)).count()
    new_admin = admin_qs.filter(date_joined__date__range=(period.start, period.end)).count()
    new_registrations = new_mobile + new_admin

    # Active accounts (is_active=True, not suspended)
    active_mobile = mobile_qs.filter(is_active=True, is_suspended=False).count()
    active_admin = admin_qs.filter(is_active=True).count()
    active_users = active_mobile + active_admin

    # 2. Approved Sellers
    approved_sellers_count = SellerRequest.objects.filter(
        status=SellerRequest.STATUS_APPROVED,
        is_suspended=False,
    ).count()

    # 3. Main Bar Graph — User Registrations by Month
    # Default to past 6 months or period window
    trend_start = period.start
    if not super_view and period.days < 180:
        trend_start = min(period.start, today.replace(day=1) - timedelta(days=150))
    monthly_buckets = _monthly_buckets(trend_start, period.end)

    monthly_labels = []
    monthly_values = []
    mobile_months, admin_months = {}, {}
    if super_view:
        from django.db.models.functions import TruncMonth
        mobile_months = {row['month'].date(): row['count'] for row in mobile_qs.filter(
            created_at__date__range=(period.start, period.end)).annotate(month=TruncMonth('created_at'))
            .values('month').annotate(count=Count('pk'))}
        admin_months = {row['month'].date(): row['count'] for row in admin_qs.filter(
            date_joined__date__range=(period.start, period.end)).annotate(month=TruncMonth('date_joined'))
            .values('month').annotate(count=Count('pk'))}
    for m_start, m_end, m_label in monthly_buckets:
        m_mobile = mobile_months.get(m_start, 0) if super_view else mobile_qs.filter(created_at__date__range=(m_start, m_end)).count()
        m_admin = admin_months.get(m_start, 0) if super_view else admin_qs.filter(date_joined__date__range=(m_start, m_end)).count()
        monthly_labels.append(m_label)
        monthly_values.append(m_mobile + m_admin)

    # 4. User Distribution Breakdown
    # Mutually exclusive account roles (seller is a privilege/status, NOT an account type)
    student_count = mobile_qs.filter(user_type=CampusHubUser.USER_TYPE_STUDENT).count()
    faculty_count = mobile_qs.filter(user_type=CampusHubUser.USER_TYPE_FACULTY).count()
    guest_count = mobile_qs.filter(user_type=CampusHubUser.USER_TYPE_GUEST).count()
    other_mobile = total_mobile - (student_count + faculty_count + guest_count)
    if other_mobile > 0 and not super_view:
        student_count += other_mobile  # default fallback to student if empty

    distribution = [
        {
            "role": "Students",
            "type_code": "student",
            "count": student_count,
            "percentage": round((student_count / total_users * 100), 1) if total_users else 0.0,
        },
        {
            "role": "Faculty & Employees",
            "type_code": "faculty",
            "count": faculty_count,
            "percentage": round((faculty_count / total_users * 100), 1) if total_users else 0.0,
        },
        {
            "role": "Guests & External",
            "type_code": "guest",
            "count": guest_count,
            "percentage": round((guest_count / total_users * 100), 1) if total_users else 0.0,
        },
        {
            "role": "Web Accounts (recorded roles)" if super_view else "Administrators & Staff",
            "type_code": "admin",
            "count": total_admin,
            "percentage": round((total_admin / total_users * 100), 1) if total_users else 0.0,
        },
    ]

    if super_view:
        distribution.append({'role': 'Unclassified', 'type_code': 'unclassified', 'count': other_mobile,
                             'percentage': round(other_mobile / total_users * 100, 1) if total_users else 0.0})
    # 5. Seller Applications & Status Breakdown
    seller_requests = SellerRequest.objects.all()
    total_seller_apps = seller_requests.count()
    seller_approved = seller_requests.filter(status=SellerRequest.STATUS_APPROVED).count()
    seller_pending = seller_requests.filter(status=SellerRequest.STATUS_PENDING).count()
    seller_revision = seller_requests.filter(status=SellerRequest.STATUS_NEEDS_REVISION).count()
    seller_rejected = seller_requests.filter(status=SellerRequest.STATUS_REJECTED).count()

    reviewed_total = seller_approved + seller_rejected
    approval_rate = round((seller_approved / reviewed_total * 100), 1) if reviewed_total else 0.0

    seller_stats = {
        "total": total_seller_apps,
        "approved": seller_approved,
        "pending": seller_pending,
        "revision": seller_revision,
        "rejected": seller_rejected,
        "approval_rate": approval_rate,
    }
    if super_view:
        for key in ('pending', 'revision', 'rejected'):
            seller_stats[key + '_share'] = round(seller_stats[key] / total_seller_apps * 100, 1) if total_seller_apps else 0
        seller_stats.update(seller_requests.aggregate(
            submitted_in_period=Count('pk', filter=Q(created_at__date__range=(period.start, period.end))),
            recorded_decisions_in_period=Count('pk', filter=Q(
                status__in=(SellerRequest.STATUS_APPROVED, SellerRequest.STATUS_REJECTED),
                reviewed_at__date__range=(period.start, period.end)))))

    return {
        "kpis": {
            "total_users": total_users,
            "new_registrations": new_registrations,
            "active_users": active_users,
            "approved_sellers": approved_sellers_count,
        },
        "main_chart": {
            "labels": monthly_labels,
            "values": monthly_values,
        },
        "chart_table": chart_table(['Month', 'Registrations in selected dates'], zip(monthly_labels, monthly_values)) if super_view else None,
        "has_registrations": new_registrations > 0,
        "inactive_users": total_users - active_users,
        "distribution": distribution,
        "seller_stats": seller_stats,
    }


def render_facility_analytics(request):
    """Render Facilities tab in Super Admin Analytics."""
    try:
        params, period = analytics_period(request)
        data = build_dashboard_data(params)
        tab_data = build_facility_tab_analytics(period, params, user=request.user)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "facility_days": period.days,
            "facility_analytics": data["facilities"],
            "facility_tab": tab_data,
        })

    return render(
        request,
        "reports/pages/admin_facility_analytics.html",
        {
            "facility_analytics": data["facilities"],
            "facility_tab": tab_data,
            "super_analytics": is_super_analytics(request.user),
            "facility_revenue_table": chart_table(['Recognition date', 'Revenue (PHP)', 'Paid transactions'], zip(
                data['facilities']['revenue_overview']['chart']['tooltip_labels'],
                [_money_text(v) for v in data['facilities']['revenue_overview']['chart']['values']],
                data['facilities']['revenue_overview']['chart']['transactions'])) if is_super_analytics(request.user) else None,
            "analytics_period": period,
            "analytics_module": "facilities",
            "analytics_links": module_links(period),
            **get_notification_context(user=request.user),
        },
    )


def render_domain_analytics(request, module):
    """Route Analytics tab requests for Facilities, Services, and Users."""
    if module == "facilities":
        from .views import admin_facility_analytics_page
        return admin_facility_analytics_page(request)

    if module not in ("services", "users"):
        return HttpResponseBadRequest("Choose a valid analytics module.")

    user = request.user
    role = (getattr(user, "role", "") or "").strip().lower()
    is_super = bool(user.is_superuser or role == "super admin")
    if not getattr(user, "is_active", False):
        raise PermissionDenied

    if module == "services":
        if not (is_super or user.has_perm("accounts.can_view_facility_analytics")):
            raise PermissionDenied
    elif module == "users":
        if not (is_super or user.has_perm("accounts.can_manage_admin_accounts")):
            raise PermissionDenied

    try:
        params, period = analytics_period(request)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))

    context = {
        "analytics_period": period,
        "analytics_module": module,
        "super_analytics": is_super_analytics(user),
        "analytics_links": module_links(period),
        **get_notification_context(user=user),
    }

    if module == "services":
        context["services_tab"] = build_services_tab_analytics(period, params, user=user)
        return render(request, "reports/pages/admin_services_analytics.html", context)
    else:
        context["users_tab"] = build_users_tab_analytics(period, params, user=user)
        return render(request, "reports/pages/admin_users_analytics.html", context)
