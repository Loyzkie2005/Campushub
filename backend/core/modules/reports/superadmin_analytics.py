"""Read-only Super Admin projections; existing metric/workflow services stay authoritative."""
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.db.models import Count, Q, Sum
from django.urls import reverse

from api.models import Booking, Product, Room
from modules.marketplace.services.analytics import valid_sales_queryset, _money_text
from .dashboard_periods import comparison_metric


def is_super_analytics(user):
    # Presentation selection only: views must still enforce their existing permissions.
    return bool(user and user.is_authenticated and user.is_active and
                (user.is_superuser or (user.role or '').strip().lower() == 'super admin'))


def chart_table(headers, rows):
    return {'headers': headers, 'rows': list(rows)}


def enrich_marketplace(analytics, user):
    """Add comparisons/accessible tables to an already authorized, unchanged sales projection."""
    period = analytics['period']
    end = period.start - timedelta(days=1)
    start = end - timedelta(days=period.days - 1)
    previous = valid_sales_queryset(user).filter(analytics_at__date__range=(start, end)).aggregate(
        revenue=Sum('total_price'), count=Count('pk'))
    revenue = Decimal(analytics['kpis']['sales'].replace(',', ''))
    label = f'previous {period.days} days ({start:%b %d, %Y} – {end:%b %d, %Y})'
    analytics['comparison'] = {
        'sales': comparison_metric(revenue, previous['revenue'] or 0, label),
        'orders': comparison_metric(analytics['kpis']['completed_orders'], previous['count'], label),
        'previous_sales': _money_text(previous['revenue']), 'previous_orders': previous['count'],
        'start': start, 'end': end,
    }
    analytics['has_sales'] = analytics['kpis']['completed_orders'] > 0
    analytics['has_positive_revenue'] = revenue > 0
    if user.has_perm('accounts.can_view_orders') or user.has_perm('accounts.can_manage_orders'):
        for row in analytics['order_status_breakdown']['rows']:
            row['url'] = reverse('admin_orders_page') + '?' + urlencode({
                'status': row['status'], 'date': 'custom',
                'date_from': period.start.isoformat(), 'date_to': period.end.isoformat()})
    if not analytics['order_status_breakdown']['total']:
        analytics['order_status_breakdown']['rows'] = []
    if user.has_perm('accounts.can_view_sellers') or user.has_perm('accounts.can_manage_sellers'):
        for row in analytics['seller_performance']['rows']:
            # Existing search, not a fabricated unique seller identifier.
            row['search_url'] = reverse('admin_sellers_page') + '?' + urlencode({'q': row['seller']})
    ids = {row['product_id'] for row in analytics['top_products'] if row['product_id']}
    ids.update(row['product_id'] for row in analytics['inventory']['all_rows'])
    products = {p.pk: p for p in Product.objects.filter(pk__in=ids).select_related('seller', 'mobile_seller')}
    can_products = user.has_perm('accounts.can_view_products') or user.has_perm('accounts.can_manage_products')
    for row in analytics['top_products']:
        product = products.get(row['product_id'])
        if can_products and product:
            row['url'] = reverse('admin_products_page') + '?' + urlencode({'product_id': product.pk})
        if product and row['seller'] == 'Not Assigned' and product.owner:
            row['seller'] = product.owner.get_full_name() or product.owner.username
    for row in analytics['inventory']['all_rows']:
        product = products.get(row['product_id'])
        row['stock_basis'] = 'Component-derived availability' if product and product.product_type == Product.TYPE_BUNDLE else 'Available quantity'
        if can_products:
            row['url'] = reverse('admin_products_page') + '?' + urlencode({'view': 'inventory', 'search': row['product']})
        if product and product.product_type == Product.TYPE_BUNDLE:
            row['action'] = 'Review component availability' if row['state'] != 'Healthy' else 'Monitor components'
    chart = analytics['sales_chart']
    analytics['sales_table'] = chart_table(['Period', 'Revenue (PHP)', 'Completed paid orders'],
        zip(chart['tooltip_labels'], [_money_text(v) for v in chart['sales']], chart['orders']))
    analytics['category_has_revenue'] = any(row['sales_value'] > 0 for row in analytics['category_sales'])
    analytics['category_table'] = chart_table(['Category', 'Revenue (PHP)', 'Revenue share (%)'],
        [(row['category'], row['sales'], row['percent']) for row in analytics['category_sales']])
    analytics['buyer_table'] = chart_table(['Period', 'Completed paid orders'],
        zip(chart['tooltip_labels'], chart['orders']))
    forecast = analytics['forecast']
    if forecast['sufficient']:
        chart = forecast['chart']
        analytics['forecast_table'] = chart_table(['Period', 'Historical units', 'Forecast units'],
            [(label, actual if actual is not None else '—', predicted if predicted is not None else '—')
             for label, actual, predicted in zip(chart['labels'], chart['historical'], chart['forecast'])])
    peak = analytics['peak_sales']['chart']
    analytics['peak_table'] = chart_table(['Recognition time interval', 'Revenue (PHP)'],
        zip(peak['labels'], [_money_text(v) for v in peak['values']]))
    return analytics


def facility_capacity_rows(period, facilities):
    """Reuse dashboard capacity calculators, with two batched queries and no new capacity assumptions."""
    from .dashboard_utilization import (VALID_STATUSES, EXCLUDED_STATUSES, CapacityUnavailable,
        _hours_or_slots, _rooms_or_units)
    ids = [f.id for f in facilities]
    days = [period.start + timedelta(days=i) for i in range(period.days)]
    bookings, rooms = defaultdict(list), defaultdict(list)
    usage = Q(booking_date__range=(period.start, period.end)) | Q(
        booking_date__lte=period.end, mobile_request__details__source='schedule',
        mobile_request__details__schedule__until__gte=period.start.isoformat()) | Q(
        check_in_date__lte=period.end, check_out_date__gt=period.start)
    for booking in Booking.objects.select_related('mobile_request').filter(
            usage, facility_id__in=ids, status__in=VALID_STATUSES):
        bookings[booking.facility_id].append(booking)
    for room in Room.objects.filter(facility_id__in=ids):
        rooms[room.facility_id].append(room)
    result = {}
    for facility in facilities:
        row = {'utilization': None, 'booked_hours': None, 'capacity_context': 'Capacity unavailable',
               'usage': '—', 'capacity': '—', 'unit': '', 'capacity_state': 'unavailable'}
        try:
            if facility.availability_status in EXCLUDED_STATUSES:
                raise CapacityUnavailable('Facility is currently unavailable; historical capacity cannot be reconstructed.')
            kind = facility.facility_type
            if kind in {'covered_court', 'function_hall', 'training_kitchen'}:
                unit = 'slots' if kind == 'training_kitchen' else 'hours'
                used, capacity = _hours_or_slots(facility, bookings[facility.id], days, slots=kind == 'training_kitchen')
            elif kind in {'hostel', 'lease_space'}:
                unit = 'units' if kind == 'lease_space' else 'room-nights'
                used, capacity = _rooms_or_units(facility, bookings[facility.id], rooms[facility.id], days, lease=kind == 'lease_space')
            else:
                raise CapacityUnavailable('Verified capacity is not configured for this facility type.')
            if capacity <= 0 or used > capacity:
                raise CapacityUnavailable('Usage/capacity cannot be verified for the selected dates.')
            row.update(utilization=round(used / capacity * 100, 1),
                booked_hours=round(used, 1) if unit == 'hours' else None,
                usage=round(used, 2), capacity=round(capacity, 2), unit=unit, capacity_state='ready',
                capacity_context=f'{used:g} of {capacity:g} {unit}; configured capacity for selected dates')
        except CapacityUnavailable as error:
            row['capacity_context'] = str(error)
        result[facility.id] = row
    return result
