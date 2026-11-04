"""Read-only Super Admin projections; existing metric/workflow services stay authoritative."""
from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal
from urllib.parse import urlencode

from django.db.models import Avg, Count, DurationField, Exists, ExpressionWrapper, F, OuterRef, Q, Sum
from django.urls import reverse
from django.utils import timezone

from api.models import Booking, InventorySKU, InventoryStockMovement, MarketplaceOrder, Product, Room
from modules.marketplace.services.analytics import valid_sales_queryset, _money_text
from modules.marketplace.services.reporting_metrics import average_order_value
from .dashboard_periods import comparison_metric


def is_super_analytics(user):
    # Presentation selection only: views must still enforce their existing permissions.
    return bool(user and user.is_authenticated and user.is_active and
                (user.is_superuser or (user.role or '').strip().lower() == 'super admin'))


def chart_table(headers, rows):
    return {'headers': headers, 'rows': list(rows)}


def submission_comparison(records, period, statuses):
    """One query compares equal-length submission cohorts using their recorded current outcomes."""
    end = period.start - timedelta(days=1)
    start = end - timedelta(days=period.days - 1)
    current = Q(created_at__date__range=(period.start, period.end))
    previous = Q(created_at__date__range=(start, end))
    fields = {'current': Count('pk', filter=current), 'previous': Count('pk', filter=previous)}
    for index, (status, _) in enumerate(statuses):
        fields[f'current_{index}'] = Count('pk', filter=current & Q(status=status))
        fields[f'previous_{index}'] = Count('pk', filter=previous & Q(status=status))
    counts = records.filter(created_at__date__range=(start, period.end)).aggregate(**fields)
    def row(label, value, prior):
        metric = comparison_metric(value, prior, f'previous {period.days} days')
        return {'label': label, 'current': value, 'previous': prior, 'difference': value - prior,
                'change': f"{metric['percentage_change']:+.1f}%" if metric['percentage_change'] is not None else ('New activity' if value else 'No change')}
    rows = [row('All submissions', counts['current'], counts['previous'])]
    rows.extend(row(label, counts[f'current_{index}'], counts[f'previous_{index}']) for index, (_, label) in enumerate(statuses))
    other_current = counts['current'] - sum(counts[f'current_{i}'] for i in range(len(statuses)))
    other_previous = counts['previous'] - sum(counts[f'previous_{i}'] for i in range(len(statuses)))
    if other_current or other_previous:
        rows.append(row('Other / unrecorded status', other_current, other_previous))
    return {'start': start, 'end': end, 'rows': rows, 'has_data': bool(counts['current'] or counts['previous'])}


def enrich_marketplace(analytics, user, *, order_grouping=None):
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
    # Reuse the recognized-sales totals and counts; no extra query or new eligibility rule.
    current_orders = analytics['kpis']['completed_orders']
    current_aov = average_order_value(revenue, current_orders)
    previous_aov = average_order_value(previous['revenue'], previous['count'])
    analytics['revenue_aov'] = {
        'current': analytics['kpis']['average_order_value'] if current_orders else None,
        'previous': _money_text(previous_aov) if previous_aov is not None else None,
        'percentage_change': comparison_metric(current_aov, previous_aov, label)['percentage_change']
            if current_aov is not None and previous_aov is not None else None,
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
            # The existing seller search supports usernames; use the stable account label when present.
            row['search_url'] = reverse('admin_sellers_page') + '?' + urlencode({'q': row.get('username') or row['seller']})
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
    enrich_marketplace_sections(analytics, user, order_grouping=order_grouping)
    return analytics


def enrich_marketplace_sections(analytics, user, *, order_grouping=None):
    """Read-only operational metrics for the existing Super Admin Marketplace tab."""
    from modules.marketplace.services.order_access import scoped_marketplace_orders
    from modules.marketplace.services.inventory import low_stock_inventory_rows
    period = analytics['period']
    orders = scoped_marketplace_orders(user).filter(created_at__date__range=(period.start, period.end))
    completed = Q(status=MarketplaceOrder.STATUS_COMPLETED)
    duration_filter = completed & Q(completed_at__isnull=False, completed_at__gte=F('created_at'))
    duration = ExpressionWrapper(F('completed_at') - F('created_at'), output_field=DurationField())
    totals = orders.aggregate(total=Count('pk'), completed=Count('pk', filter=completed),
        cancelled=Count('pk', filter=Q(status=MarketplaceOrder.STATUS_CANCELLED)),
        paid=Count('pk', filter=Q(payment_status=MarketplaceOrder.PAYMENT_PAID)),
        unpaid=Count('pk', filter=Q(payment_status=MarketplaceOrder.PAYMENT_UNPAID)),
        pickup=Count('pk', filter=Q(fulfillment_method='pickup')),
        delivery=Count('pk', filter=Q(fulfillment_method='seller_delivery')),
        timed=Count('pk', filter=duration_filter), average=Avg(duration, filter=duration_filter))
    total = totals['total']
    percentage = lambda count: round(count / total * 100, 1) if total else None
    def breakdown(rows):
        return [{'label': label, 'count': count, 'percentage': percentage(count)} for label, count in rows]
    payment = breakdown([('Paid', totals['paid']), ('Unpaid', totals['unpaid']),
                         ('Not recorded / other', total - totals['paid'] - totals['unpaid'])])
    fulfillment = breakdown([('Customer Pickup', totals['pickup']), ('Seller Delivery', totals['delivery']),
                             ('Not recorded / other', total - totals['pickup'] - totals['delivery'])])
    analytics['operations'] = {**totals, 'average': None,
        'completion_rate': percentage(totals['completed']), 'cancellation_rate': percentage(totals['cancelled']),
        'processing_hours': round(totals['average'].total_seconds() / 3600, 2) if totals['average'] is not None else None,
        'payment': payment, 'fulfillment': fulfillment}
    analytics['payment_chart'] = {'labels': [r['label'] for r in payment], 'values': [r['count'] for r in payment]}
    analytics['fulfillment_chart'] = {'labels': [r['label'] for r in fulfillment], 'values': [r['count'] for r in fulfillment]}
    analytics['payment_table'] = chart_table(['Payment status', 'Orders', 'Share (%)'],
        [(r['label'], r['count'], r['percentage']) for r in payment])
    analytics['fulfillment_table'] = chart_table(['Fulfillment method', 'Orders', 'Share (%)'],
        [(r['label'], r['count'], r['percentage']) for r in fulfillment])
    demand = request_demand(orders, period, grouping=order_grouping, include_empty=True)
    analytics['order_volume'] = {**demand, 'table': chart_table(
        [demand['unit'], 'Submitted orders'], zip(demand['chart']['labels'], demand['chart']['values']))}
    analytics['submission_comparison'] = submission_comparison(scoped_marketplace_orders(user), period, MarketplaceOrder.STATUS_CHOICES)

    # Stable current owner IDs keep web/mobile sellers distinct. Missing owners stay unclassified.
    from modules.marketplace.services.analytics import seller_identity_annotations
    owner_fields = ['analytics_seller_source', 'analytics_seller_id', 'analytics_seller_first_name',
                    'analytics_seller_last_name', 'analytics_seller_username']
    seller_rows = []
    for row in orders.annotate(**seller_identity_annotations(include_names=True)).values(*owner_fields).annotate(total=Count('pk'), completed=Count('pk', filter=completed),
            cancelled=Count('pk', filter=Q(status=MarketplaceOrder.STATUS_CANCELLED)),
            pickup=Count('pk', filter=completed & Q(fulfillment_method='pickup')),
            delivery=Count('pk', filter=completed & Q(fulfillment_method='seller_delivery')),
            timed=Count('pk', filter=duration_filter), average=Avg(duration, filter=duration_filter)).order_by():
        name = ' '.join(filter(None, [row['analytics_seller_first_name'], row['analytics_seller_last_name']])).strip()
        key = f"{row['analytics_seller_source']}:{row['analytics_seller_id']}" if row['analytics_seller_id'] else 'unrecorded'
        seller_rows.append({'seller': name or row['analytics_seller_username'] or 'Seller not recorded',
            'seller_key': key, 'username': row['analytics_seller_username'] or '',
            'total': row['total'], 'completed': row['completed'], 'cancelled': row['cancelled'],
            'pickup': row['pickup'], 'delivery': row['delivery'], 'timed': row['timed'],
            'completion_rate': round(row['completed'] / row['total'] * 100, 1),
            'processing_hours': round(row['average'].total_seconds() / 3600, 2) if row['average'] is not None else None})
    seller_rows.sort(key=lambda r: (-r['completed'], -r['total'], r['seller'].lower()))
    analytics['seller_fulfillment'] = seller_rows[:10]
    ranking = analytics['seller_performance']['rows']
    analytics['seller_ranking_chart'] = {'labels': [r['seller'] for r in ranking], 'values': [r['sales_value'] for r in ranking]}
    analytics['seller_ranking_has_revenue'] = any(r['sales_value'] > 0 for r in ranking)

    sales = valid_sales_queryset(user).filter(analytics_at__date__range=(period.start, period.end))
    analytics['variant_sales'] = marketplace_variant_sales(sales, recorded_only=True)
    ids = [row['product_id'] for row in analytics['inventory']['all_rows']]
    products = Product.objects.filter(pk__in=ids)
    can_products = user.has_perm('accounts.can_view_products') or user.has_perm('accounts.can_manage_products')
    alerts = low_stock_inventory_rows(products, limit=10, include_out_of_stock=True)
    analytics['stock_alerts'] = [{'product': row['product'].name,
        'variant': ' / '.join(filter(None, [row['group_name'], row['variant_name']])) or 'Standard stock',
        'available': row['available'], 'threshold': row['threshold'],
        'status': 'Out of Stock' if row['available'] == 0 else 'Low Stock',
        'url': reverse('admin_products_page') + '?' + urlencode({'product_id': row['product'].pk}) if can_products else None}
        for row in alerts]
    forecast = analytics['forecast']
    analytics['restock'] = {'forecast_ready': bool(forecast.get('sufficient') and forecast.get('operational') and not forecast.get('inventory_review')),
        'historical': bool(forecast.get('sufficient') and not forecast.get('operational')),
        'inventory_review': bool(forecast.get('inventory_review')), 'threshold_alerts': len(alerts)}
    analytics['stock_turnover'] = marketplace_stock_turnover(products, sales, period)
    analytics['turnover_supported'] = [r for r in analytics['stock_turnover'] if r['turnover'] is not None or r['sell_through'] is not None]
    analytics['turnover_unavailable'] = len(analytics['stock_turnover']) - len(analytics['turnover_supported'])
    analytics['restock_rows'] = [r for r in analytics['inventory']['all_rows']
        if r['state'] in {'Low Stock', 'Out of Stock'}][:10]


def marketplace_variant_sales(sales, *, recorded_only=False):
    """Group recorded selection combinations once per order; never multiply its revenue per option."""
    from modules.marketplace.services.customization import parse_order_selections
    grouped = {}
    for row in sales.values('product_id', 'product_name', 'customization', 'option').annotate(
            units=Sum('quantity'), sales=Sum('total_price'), orders=Count('pk')).order_by():
        try:
            selections = parse_order_selections(row['customization'])
        except (AttributeError, TypeError, ValueError):
            selections = []  # Malformed legacy selections do not identify a variant.
        label = ' / '.join(sorted({f"{r['group']}: {r['option']}" for r in selections}))
        label = label or str(row['option'] or '').strip()
        if recorded_only and not label:
            continue
        label = label or 'No variant recorded'
        key = (row['product_id'], row['product_name'], label)
        item = grouped.setdefault(key, {'product': row['product_name'], 'variant': label,
            'units': 0, 'orders': 0, 'amount': Decimal('0')})
        item['units'] += row['units']; item['orders'] += row['orders']; item['amount'] += row['sales']
    rows = sorted(grouped.values(), key=lambda r: (-r['units'], -r['amount'], r['product'], r['variant']))
    return [{**r, 'sales': _money_text(r['amount'])} for r in rows[:10]]


def marketplace_stock_turnover(products, sales, period):
    """Unit turnover for up to ten current physical SKUs with a continuous observed on-hand ledger."""
    from modules.marketplace.services.inventory_records import stock_points
    start = timezone.make_aware(datetime.combine(period.start, time.min))
    end = min(timezone.make_aware(datetime.combine(period.end + timedelta(days=1), time.min)), timezone.now())
    if end <= start:
        return []
    skus = []
    for sku in InventorySKU.objects.filter(product__in=products, product__product_type=Product.TYPE_SINGLE).select_related('product').order_by('product__name', 'pk').iterator():
        points = stock_points(sku.product.stock, sku.product.customization_options, sku.product.product_type)
        if (sku.group_name, sku.variant_name) in points:
            skus.append(sku)
        if len(skus) == 10:
            break
    ids = [s.pk for s in skus]
    physical_event = Q(balance='on_hand') | Q(balance='available', kind__in=('opening', 'receipt', 'adjustment', 'sale'))
    baseline = {r.sku_id: r for r in InventoryStockMovement.objects.filter(physical_event, sku_id__in=ids,
        created_at__lt=start).order_by('sku_id', '-created_at', '-pk').distinct('sku_id')}
    events = defaultdict(list)
    for movement in InventoryStockMovement.objects.filter(physical_event, sku_id__in=ids,
            created_at__gte=start, created_at__lt=end).annotate(
            eligible_sale=Exists(sales.filter(pk=OuterRef('order_id')))).order_by('created_at', 'pk'):
        events[movement.sku_id].append(movement)
    rows = []
    for sku in skus:
        row = {'product': sku.product.name, 'variant': ' / '.join(filter(None, [sku.group_name, sku.variant_name])) or 'Standard stock',
               'average_stock': None, 'units': None, 'turnover': None, 'sell_through': None,
               'message': 'Insufficient verified on-hand history for the selected dates.'}
        initial = baseline.get(sku.pk)
        if initial and initial.balance == 'on_hand' and initial.available_after is not None:
            balance, cursor, weighted, units, additions = initial.available_after, start, 0, 0, 0
            valid = True
            for event in events[sku.pk]:
                if (event.balance != 'on_hand' or event.available_before != balance or event.available_after is None or
                        event.available_after != balance + event.quantity_change or event.available_after < 0):
                    valid = False; break
                weighted += balance * (event.created_at - cursor).total_seconds()
                additions += max(event.quantity_change, 0)
                if event.kind == 'sale' and event.quantity_change < 0 and event.eligible_sale:
                    units -= event.quantity_change
                balance, cursor = event.available_after, event.created_at
            if valid:
                weighted += balance * (end - cursor).total_seconds()
                average = weighted / (end - start).total_seconds()
                supply = initial.available_after + additions
                row.update(units=units, sell_through=round(units / supply * 100, 1) if supply > 0 else None)
                if average > 0:
                    row.update(average_stock=round(average, 2), units=units,
                        turnover=round(units / average, 2), message='Verified physical units / time-weighted on-hand stock')
                else:
                    row['message'] = 'No positive average on-hand balance; turnover cannot be calculated.'
        rows.append(row)
    return rows


def request_timing(queryset):
    """Use dedicated recorded workflow timestamps; updated_at is never a completion proxy."""
    from django.utils.dateparse import parse_datetime
    approval, completion = [], []
    now = timezone.now()
    for row in queryset.values('created_at', 'status', 'mobile_request__details').iterator():
        details = row['mobile_request__details']
        if not isinstance(details, dict):
            continue
        for key, output in (('approval', approval), ('completion', completion)):
            record = details.get(key)
            if not isinstance(record, dict) or (key == 'completion' and row['status'] != Booking.STATUS_COMPLETED):
                continue
            try:
                stamp = parse_datetime(record.get('at') or '')
                if stamp and timezone.is_aware(stamp) and row['created_at'] <= stamp <= now:
                    output.append((stamp - row['created_at']).total_seconds() / 3600)
            except (TypeError, ValueError, OverflowError):
                continue
    return {'approval_hours': round(sum(approval) / len(approval), 2) if approval else None,
            'approval_timed': len(approval),
            'completion_hours': round(sum(completion) / len(completion), 2) if completion else None,
            'completion_timed': len(completion)}


def request_demand(queryset, period, *, grouping=None, include_empty=False):
    """One date aggregation; charts include only the selected submission dates."""
    from django.db.models.functions import TruncDate
    daily = list(queryset.annotate(day=TruncDate('created_at')).values('day').annotate(total=Count('pk')).order_by('day'))
    automatic = 'monthly' if period.days > 90 else 'weekly' if period.days > 31 else 'daily'
    grouping = grouping if grouping in ('daily', 'weekly', 'monthly') else automatic
    def bucket_for(day):
        return day.replace(day=1) if grouping == 'monthly' else day - timedelta(days=day.weekday()) if grouping == 'weekly' else day
    buckets, weekdays = defaultdict(int), defaultdict(int)
    if include_empty:
        day = period.start
        while day <= period.end:
            buckets[bucket_for(day)] = 0
            day += timedelta(days=1)
    for row in daily:
        day = row['day']; weekdays[day.weekday()] += row['total']
        bucket = bucket_for(day)
        buckets[bucket] += row['total']
    unit = 'Month' if grouping == 'monthly' else 'Week beginning' if grouping == 'weekly' else 'Date'
    chart = {'labels': [d.strftime('%b %d, %Y') for d in sorted(buckets)], 'values': [buckets[d] for d in sorted(buckets)]}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday = {'labels': days, 'values': [weekdays[i] for i in range(7)]}
    result = {'chart': chart, 'table': chart_table([unit, 'Submitted requests'], zip(chart['labels'], chart['values'])),
            'weekday_chart': weekday, 'weekday_table': chart_table(['Submission weekday', 'Requests'], zip(days, weekday['values'])),
            'unit': unit, 'has_data': bool(daily)}
    if include_empty:
        result['grouping'] = grouping
    return result


def enrich_facilities(data, period):
    from .dashboard_bookings import booking_request_records
    records = booking_request_records()
    requests = records.filter(created_at__date__range=(period.start, period.end))
    data['submission_comparison'] = submission_comparison(records, period, Booking.STATUS_CHOICES)
    counts = requests.aggregate(total=Count('pk'), accepted=Count('pk', filter=Q(status__in=('approved', 'completed'))),
        rejected=Count('pk', filter=Q(status='rejected')), pending=Count('pk', filter=Q(status='pending')))
    reviewed = counts['accepted'] + counts['rejected']
    data['approval'] = {**counts, 'rate': round(counts['accepted'] / reviewed * 100, 1) if reviewed else None,
                        **request_timing(requests)}
    data['demand'] = request_demand(requests, period)


def enrich_services(data, period):
    from .dashboard_bookings import booking_request_records
    records = booking_request_records(services=True)
    requests = records.filter(created_at__date__range=(period.start, period.end))
    data['submission_comparison'] = submission_comparison(records, period, Booking.STATUS_CHOICES)
    total = data['kpis']['total_requests']
    data['performance'] = {**request_timing(requests),
        'completion_rate': round(data['kpis']['completed_requests'] / total * 100, 1) if total else None}
    data['demand'] = request_demand(requests, period)
    data['distribution_chart'] = {'labels': [r['facility__facility_name'] for r in data['breakdown']],
                                   'values': [r['total'] for r in data['breakdown']]}
    data['distribution_table'] = chart_table(['Service', 'Submitted requests'], zip(data['distribution_chart']['labels'], data['distribution_chart']['values']))
    data['pending'] = list(requests.filter(status='pending').order_by('created_at', 'pk').values(
        'pk', 'facility__facility_name', 'facility_id', 'created_at')[:5])
    for row in data['pending']:
        row['url'] = reverse('admin_service_requests_page') + '?' + urlencode({'service': row['facility_id'], 'q': row['pk']})


def enrich_users(data, period):
    from accounts.models import AccountActivity, User
    from api.models import CampusHubUser
    from modules.facilities.services.schedules import schedule_blocks_q
    total = data['kpis']['total_users']
    verified = User.objects.filter(email_verified=True).count() + CampusHubUser.objects.filter(email_verified=True).count()
    previous_end = period.start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period.days - 1)
    previous = User.objects.filter(date_joined__date__range=(previous_start, previous_end)).count() + CampusHubUser.objects.filter(
        created_at__date__range=(previous_start, previous_end)).count()
    signins = AccountActivity.objects.filter(activity_type='login_success', result='success',
        created_at__date__range=(period.start, period.end)).filter(
        Q(account_source='admin', account_id__in=User.objects.values('pk')) |
        Q(account_source='mobile', account_id__in=CampusHubUser.objects.values('pk'))).aggregate(
        events=Count('pk'), web=Count('account_id', distinct=True, filter=Q(account_source='admin')),
        mobile=Count('account_id', distinct=True, filter=Q(account_source='mobile')))
    data['verification'] = {'verified': verified, 'total': total, 'rate': round(verified / total * 100, 1) if total else None}
    data['growth'] = {**comparison_metric(data['kpis']['new_registrations'], previous, f'previous {period.days} days'),
                      'previous': previous, 'start': previous_start, 'end': previous_end}
    data['engagement'] = {'signin_events': signins['events'], 'signin_accounts': signins['web'] + signins['mobile'],
        'request_accounts': Booking.objects.exclude(schedule_blocks_q()).filter(
            created_at__date__range=(period.start, period.end), user_id__isnull=False).values('user_id').distinct().count()}
    data['distribution_chart'] = {'labels': [r['role'] for r in data['distribution']], 'values': [r['count'] for r in data['distribution']]}
    data['distribution_table'] = chart_table(['Recorded account category', 'Accounts', 'Share (%)'],
        [(r['role'], r['count'], r['percentage']) for r in data['distribution']])


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
