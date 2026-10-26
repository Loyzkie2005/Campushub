"""Read-only operational projection for the existing Facility Admin dashboard."""
from datetime import time, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.db.models import Case, Count, DateField, F, Q, Sum, When
from django.db.models.functions import Length, Trim
from django.db.models.fields.json import KeyTextTransform
from django.urls import reverse
from django.utils import timezone

from accounts.models import AccountActivity
from api.models import Booking, Facility, FacilityBookingRequest
from modules.facilities.revenue import valid_facility_payments
from modules.facilities.services.booking_workflow import paid_summary, status_label, time_label
from modules.facilities.services.calendar import calendar_events
from modules.facilities.services.catalog import service_resources_q
from modules.facilities.services.facility_configuration import normalize_facility_status
from modules.facilities.services.schedules import schedule_blocks_q
from .dashboard_bookings import build_booking_overview


def _booking_row(booking):
    person = booking.user
    requester = ' '.join(filter(None, [getattr(person, 'first_name', ''), getattr(person, 'last_name', '')]))
    if booking.check_in_date:
        date = f'{booking.check_in_date:%b %d, %Y}'
        slot = f'Check-out {booking.check_out_date:%b %d, %Y}' if booking.check_out_date else 'Check-out not recorded'
    else:
        date = booking.booking_date.strftime('%b %d, %Y') if booking.booking_date else 'Date not recorded'
        slot = f'{time_label(booking.start_time)} – {time_label(booking.end_time)}' if booking.start_time and booking.end_time else 'Time not recorded'
    return {'id': booking.pk, 'requester': requester or getattr(person, 'username', '') or 'Requester not recorded',
            'facility_name': booking.facility.facility_name, 'date': date, 'requested_date': date,
            'time': slot, 'status': status_label(booking, paid_summary(booking)), 'status_key': booking.status,
            'url': reverse('admin_booking_details_page', args=[booking.pk])}


def _conflict_count(events):
    """Count overlapping calendar occurrences, respecting separate room units."""
    from .views import _count_booking_conflicts
    grouped = {}
    for event in events:
        grouped.setdefault((event['facility_id'], event['date']), []).append(event)
    count = 0
    for (facility, day), rows in grouped.items():
        for index, left in enumerate(rows):
            for right in rows[index + 1:]:
                if left['id'] == right['id']:
                    continue
                if left.get('room_id') and right.get('room_id') and left['room_id'] != right['room_id']:
                    continue
                slots = []
                for row in (left, right):
                    whole_day = row.get('all_day') or row.get('end_date')
                    slots.append({'facility_id': facility, 'booking_date': day,
                                  'start_time': time.min if whole_day else time.fromisoformat(row['start'] or '00:00'),
                                  'end_time': time.max if whole_day else time.fromisoformat(row['end'] or '23:59:59')})
                count += _count_booking_conflicts(slots)
    return count


def facility_admin_dashboard(request, user):
    now = timezone.localtime()
    today = now.date()
    grouping = request.GET.get('booking_grouping', 'daily')
    if grouping not in ('daily', 'weekly', 'monthly'):
        grouping = 'daily'
    default_days = {'daily': 7, 'weekly': 84, 'monthly': 365}[grouping]
    try:
        days = int(request.GET.get('booking_days', default_days))
    except (TypeError, ValueError):
        days = default_days
    if days not in (7, 14, 30, 84, 365):
        days = default_days
    period = SimpleNamespace(start=today - timedelta(days=days - 1), end=today, days=days)

    physical_facilities = Facility.objects.exclude(service_resources_q())
    facilities = physical_facilities.filter(is_archived=False).order_by('facility_name', 'pk')
    # Archiving hides operational items; it must not erase historical chart/receipt totals.
    records = Booking.objects.filter(facility_id__in=physical_facilities.values('pk')).exclude(schedule_blocks_q())
    archived = FacilityBookingRequest.objects.filter(details__archive__is_archived=True).values('booking_id')
    current = records.exclude(pk__in=archived).filter(facility__is_archived=False)
    pending = current.filter(status=Booking.STATUS_PENDING)
    stays = Q(check_in_date__gte=today, check_out_date__gt=F('check_in_date'))
    slots = Q(check_in_date__isnull=True, check_out_date__isnull=True) & (
        Q(booking_date__gt=today) | Q(booking_date=today, start_time__gte=now.time().replace(tzinfo=None)) |
        Q(booking_date=today, start_time__isnull=True))
    upcoming = current.filter(stays | slots, status=Booking.STATUS_APPROVED).annotate(
        reservation_day=Case(When(check_in_date__isnull=False, then=F('check_in_date')),
                             default=F('booking_date'), output_field=DateField())).order_by('reservation_day', 'start_time', 'pk')
    totals = records.filter(created_at__date__range=(period.start, period.end)).aggregate(
        current=Count('pk'), period_pending=Count('pk', filter=Q(status=Booking.STATUS_PENDING)),
        period_approved=Count('pk', filter=Q(status=Booking.STATUS_APPROVED)),
        period_completed=Count('pk', filter=Q(status=Booking.STATUS_COMPLETED)),
        period_rejected_cancelled=Count('pk', filter=Q(status__in=(Booking.STATUS_REJECTED, Booking.STATUS_CANCELLED))))
    trend = build_booking_overview(period, totals, {}, grouping=grouping, records=records)
    facility_list = []
    for facility in facilities:
        status = normalize_facility_status(facility.availability_status)
        facility_list.append({'id': facility.pk, 'name': facility.facility_name,
                              'type': facility.custom_facility_type or facility.get_facility_type_display(),
                              'status': dict(Facility.STATUS_CHOICES).get(status, 'Status not recorded'), 'status_key': status})
    maintenance = sum(row['status_key'] == Facility.STATUS_MAINTENANCE for row in facility_list)
    unavailable = sum(row['status_key'] == Facility.STATUS_UNAVAILABLE for row in facility_list)
    # Existing calendar projection expands academic/maintenance blocks and stays without writes.
    facility_ids = {row['id'] for row in facility_list}
    archived_ids = set(archived.values_list('booking_id', flat=True))
    events = [row for row in calendar_events(today, today + timedelta(days=30), now=now)
              if row['facility_id'] in facility_ids and row['id'] not in archived_ids]
    conflicts = _conflict_count(events)
    today_count = current.filter(status__in=(Booking.STATUS_APPROVED, Booking.STATUS_COMPLETED)).filter(
        Q(booking_date=today, check_in_date__isnull=True) | Q(check_in_date__lte=today, check_out_date__gt=today)).count()

    may_read_payments = any(user.has_perm('accounts.' + perm) for perm in
                            ('can_record_facility_payment', 'can_view_facility_reports', 'can_manage_bookings'))
    payment_stats = {'total_collected': '0.00', 'recent_receipts': []}
    if may_read_payments:
        # Paid is the existing staff-verified payment state; require recorded OR evidence too.
        payments = valid_facility_payments().filter(booking_id__in=records.values('pk')).annotate(
            receipt_length=Length(Trim('official_receipt_no'))).filter(receipt_length__gt=0)
        payment_stats['total_collected'] = f"{payments.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0'):.2f}"
        payment_stats['recent_receipts'] = [{'or_number': p.official_receipt_no, 'booking_id': p.booking_id,
            'facility_name': p.booking.facility.facility_name, 'amount': f'{p.paid_amount:.2f}',
            'date': p.paid_at or p.created_at, 'url': reverse('admin_booking_details_page', args=[p.booking_id]) + '?tab=Payment'}
            for p in payments.select_related('booking__facility').order_by('-revenue_date', '-created_at', '-pk')[:5]]

    activity = AccountActivity.objects.filter(module__in=('Facilities', 'Facility Bookings')).annotate(
        facility_ref=KeyTextTransform('facility_id', 'metadata'),
        booking_ref=KeyTextTransform('booking_id', 'metadata')).filter(
        Q(facility_ref__in=physical_facilities.values('pk')) | Q(booking_ref__in=records.values('pk')))
    activities = [{'message': item.activity, 'performed_by': item.full_name or item.username or 'Recorded user',
                   'date': item.created_at} for item in activity.order_by('-created_at', '-pk')[:6]]
    related = current.select_related('facility', 'user', 'mobile_request').prefetch_related('payments')
    return {'total_facilities': len(facility_list), 'pending_bookings': pending.count(),
            'upcoming_reservations_count': upcoming.count(), 'maintenance_facilities': maintenance,
            'pending_requests': [_booking_row(b) for b in related.filter(pk__in=pending.values('pk')).order_by('created_at', 'pk')[:6]],
            'upcoming_reservations': [_booking_row(b) for b in upcoming.select_related('facility', 'user', 'mobile_request').prefetch_related('payments')[:6]],
            'facilities_list': facility_list, 'booking_days': days, 'booking_grouping': grouping,
            'booking_chart': trend['chart'], 'period_bookings_sum': trend['total'],
            'booking_period_label': f'{period.start:%b %d, %Y} – {period.end:%b %d, %Y}',
            'schedule_overview': {'bookings_today': today_count, 'detected_conflicts': conflicts,
                'maintenance_count': maintenance, 'unavailable_count': unavailable,
                'has_issues': bool(conflicts or maintenance or unavailable)},
            'payment_stats': payment_stats, 'can_view_payments': may_read_payments, 'activities': activities}
