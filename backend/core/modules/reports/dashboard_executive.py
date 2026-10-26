"""Bounded executive summaries over existing service, booking and audit records."""
from urllib.parse import urlencode
from datetime import timedelta
from django.db.models import Count, F, Q
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.formats import date_format
from django.utils import timezone
from accounts.activity_service import format_activities
from accounts.models import AccountActivity
from api.models import Booking, Facility
from modules.facilities.services.booking_workflow import payment_summary_query
from modules.facilities.services.catalog import service_resources_q
from modules.facilities.services.schedules import schedule_blocks_q
from .dashboard_bookings import build_booking_overview


def users_overview(period):
    """Summarize recorded registrations and actual mobile account types, without RBAC inference."""
    from accounts.models import User
    from api.models import CampusHubUser
    days = {}
    for model, field in ((User, 'date_joined'), (CampusHubUser, 'created_at')):
        rows = (model.objects.filter(**{field + '__date__range': (period.start, period.end)})
                .order_by().annotate(day=TruncDate(field)).values('day').annotate(count=Count('pk')))
        for row in rows:
            days[row['day']] = days.get(row['day'], 0) + row['count']
    trend = []
    for offset in range(period.days):
        day = period.start + timedelta(days=offset)
        trend.append({'date': day.isoformat(), 'label': day.strftime('%b %d, %Y'), 'count': days.get(day, 0)})
    recorded = list(CampusHubUser.objects.order_by().values('user_type').annotate(
        count=Count('pk'), verified=Count('pk', filter=Q(email_verified=True))))
    types = dict(CampusHubUser.USER_TYPE_CHOICES)
    typed_total = sum(row['count'] for row in recorded if row['user_type'] in types)
    distribution = [{'name': types[row['user_type']], 'count': row['count'],
                     'percentage': round(row['count'] / typed_total * 100, 1)}
                    for row in recorded if row['user_type'] in types and row['count']]
    distribution.sort(key=lambda row: (-row['count'], row['name']))
    return {'new_registrations': sum(days.values()),
            'verified_users': User.objects.filter(email_verified=True).count() + sum(row['verified'] for row in recorded),
            'trend': trend, 'distribution': distribution,
            'untyped': sum(row['count'] for row in recorded if row['user_type'] not in types)}


def service_overview(period, *, current_counts=None, grouping='daily'):
    """Current service capacity/pending queue; submitted-period request performance."""
    requests = Booking.objects.filter(service_resources_q('facility__')).exclude(schedule_blocks_q())
    selected = requests.filter(created_at__date__range=(period.start, period.end))
    from .analytics_sections import service_request_breakdown
    counts = selected.aggregate(
        total_requests=Count('pk'),
        approved_requests=Count('pk', filter=Q(status=Booking.STATUS_APPROVED)),
        closed_requests=Count('pk', filter=Q(status__in=(Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED))),
        open_requests=Count('pk', filter=Q(status__in=(Booking.STATUS_PENDING, Booking.STATUS_APPROVED))),
        pending_requests=Count('pk', filter=Q(status=Booking.STATUS_PENDING)),
        completed_requests=Count('pk', filter=Q(status=Booking.STATUS_COMPLETED)))
    active = current_counts['active_services'] if current_counts is not None else Facility.objects.filter(
        service_resources_q(), is_archived=False, availability_status=Facility.STATUS_AVAILABLE).count()
    popular = (selected.filter(status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED))
               .values('facility_id', 'facility__facility_name').annotate(count=Count('pk'))
               .order_by('-count', 'facility__facility_name', 'facility_id').first())
    def rows(query):
        from accounts.views import _booking_display_fields
        return [{'id': row.pk, 'service': row.facility.facility_name,
                 'requester': _booking_display_fields(row)[1] or 'Not recorded',
                 'status': row.get_status_display(), 'submitted_at': row.created_at.isoformat(),
                 'url': reverse('admin_service_requests_page') + '?' + urlencode({'service': row.facility_id, 'q': row.pk})}
                for row in query.select_related('facility', 'user').order_by('-created_at', 'pk')[:5]]
    pending = requests.filter(status=Booking.STATUS_PENDING)
    pending_rows = rows(pending)
    # Reuse the existing five-status bucketing, with only the service request queryset.
    series = build_booking_overview(period, {
        'current': counts['total_requests'], 'period_pending': counts['pending_requests'],
        'period_approved': counts['approved_requests'], 'period_completed': counts['completed_requests'],
        'period_rejected_cancelled': counts['closed_requests'],
    }, {}, records=requests, grouping=grouping)
    unavailable = list(Facility.objects.filter(service_resources_q(), is_archived=False,
        availability_status__in=(Facility.STATUS_UNAVAILABLE, Facility.STATUS_MAINTENANCE,
                                 Facility.STATUS_RESERVED, Facility.STATUS_OCCUPIED))
        .order_by('facility_name', 'pk').values('id', 'facility_name', 'availability_status')[:2])
    attention = [{'reference': row['id'], 'service': row['service'], 'status': row['status'],
                  'reason': 'Review this service request.', 'url': row['url'], 'date': row['submitted_at']}
                 for row in pending_rows[:5-len(unavailable)]]
    attention.extend({'reference': row['id'], 'service': row['facility_name'],
        'status': dict(Facility.STATUS_CHOICES)[row['availability_status']], 'reason': 'Review service availability in the catalog.',
        'url': reverse('admin_services_page') + '?' + urlencode({'status': row['availability_status']}), 'date': None}
        for row in unavailable)
    return {**counts, 'active_services': active, 'most_requested': (
        {'name': popular['facility__facility_name'], 'count': popular['count']} if popular else None),
        'recent_requests': rows(selected), 'pending_queue': pending_rows,
        'request_trend': {key: series[key] for key in ('total', 'trend', 'grouping', 'start_date', 'end_date')},
        'requests_by_service': service_request_breakdown(selected, limit=5, by_id=True), 'attention': attention,
        'pending_current': current_counts['pending_current'] if current_counts is not None else pending.count()}


def executive_overview(period, comparison, *, grouping='daily', services_current=None, service_grouping='daily'):
    """Physical reservations reuse the booking chart and recorded-payment SQL helper."""
    from .dashboard_periods import comparison_metric
    physical = Booking.objects.exclude(schedule_blocks_q()).exclude(service_resources_q('facility__'))
    current = Q(created_at__date__range=(period.start, period.end))
    previous = Q(created_at__date__range=(comparison['previous_start_date'], comparison['previous_end_date']))
    totals = physical.aggregate(current=Count('pk', filter=current), previous=Count('pk', filter=previous),
        period_pending=Count('pk', filter=current & Q(status=Booking.STATUS_PENDING)),
        period_approved=Count('pk', filter=current & Q(status=Booking.STATUS_APPROVED)),
        period_completed=Count('pk', filter=current & Q(status=Booking.STATUS_COMPLETED)),
        period_rejected_cancelled=Count('pk', filter=current & Q(status__in=(Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED))))
    booking = build_booking_overview(period, totals,
        comparison_metric(totals['current'], totals['previous'], comparison['comparison_label']),
        records=physical, grouping=grouping)
    # Matches booking_workflow.status_label: Approved + fully recorded paid payments.
    booking['reserved_confirmed'] = payment_summary_query(physical.filter(current, status=Booking.STATUS_APPROVED)).filter(
        has_paid=True, paid_total__gte=F('total_amount')).count()
    selected = AccountActivity.objects.filter(created_at__date__range=(period.start, period.end)).order_by('-created_at', '-pk')[:5]
    current_year = timezone.localdate().year
    def activity_time_label(value):
        stamp = timezone.localtime(parse_datetime(value))
        return date_format(stamp, 'M j, g:i A' if stamp.year == current_year else 'M j, Y, g:i A')
    activities = [{'time': row['date_time'], 'time_label': activity_time_label(row['date_time']),
                   'module': row['module'], 'activity': row['action'], 'user': row['performed_by']['name'],
                   'result': row['result'], 'details_url': reverse('activity_log_detail', kwargs={'pk': row['id']})}
                  for row in format_activities(selected, scoped=True, include_targets=False)]
    dates = {'period': 'custom', 'start_date': period.start.isoformat(), 'end_date': period.end.isoformat()}
    urls = {module: reverse('admin_marketplace_analytics_page') + '?' + urlencode({**dates, 'module': module,
            'date_from': period.start.isoformat(), 'date_to': period.end.isoformat()})
            for module in ('marketplace', 'facilities', 'services', 'users')}
    return {'booking_overview': booking, 'services': service_overview(period, current_counts=services_current, grouping=service_grouping),
            'activities': activities, 'analytics_urls': urls, 'users': users_overview(period)}
