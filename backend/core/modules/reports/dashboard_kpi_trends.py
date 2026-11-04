"""Equal-length activity comparisons scoped to the four System Overview KPIs."""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP


def comparison_dates(period):
    """Inclusive local dates: immediately preceding, nonoverlapping, equal days."""
    end = period.start - timedelta(days=1)
    start = end - timedelta(days=period.days - 1)
    return start, end


def activity_trend(current, previous, period, *, basis, context):
    """JSON-ready presentation; direction measures change, never operational success."""
    current, previous = Decimal(str(current)), Decimal(str(previous))
    previous_start, previous_end = comparison_dates(period)
    percentage = (current - previous) / previous * 100 if previous else None
    percentage_value = float(percentage.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) if percentage is not None else None
    if percentage is None:
        label, direction = ('↗ New Activity', 'up') if current else ('', 'neutral')
    elif percentage_value == 0:
        label, direction = '', 'neutral'
    else:
        magnitude = abs(percentage).quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
        text = format(magnitude, 'f').rstrip('0').rstrip('.') if magnitude else '<0.1'
        label = ('+' if percentage > 0 else '−') + text + '%'
        direction = 'up' if percentage > 0 else 'down'
    explanation = (f'{basis}: {current:,} in {period.start.isoformat()} to {period.end.isoformat()}; '
                   f'{previous:,} in {previous_start.isoformat()} to {previous_end.isoformat()} '
                   f'(Asia/Manila, {period.days} days each). {context} '
                   'Activity change describes volume, not a judgement of business success.')
    return {'current_value': float(current), 'previous_value': float(previous),
            'percentage_change': percentage_value,
            'label': label, 'visible': bool(label), 'direction': direction, 'basis': basis, 'explanation': explanation,
            'start_date': period.start.isoformat(), 'end_date': period.end.isoformat(),
            'previous_start_date': previous_start.isoformat(), 'previous_end_date': previous_end.isoformat(),
            'days': period.days, 'timezone': 'Asia/Manila'}


def attach_kpi_trends(kpis, period, *, new_users, previous_users, previous_bookings, previous_orders, current_sales, previous_sales):
    """Reuse existing database aggregates without issuing additional queries.

    Called under build_dashboard_data's Asia/Manila timezone override. Lifetime
    account totals and every existing API field remain independent of growth.
    """
    rows = (
        ('total_users', new_users, previous_users, 'New user registrations'),
        ('total_orders', kpis['total_orders']['value'], previous_orders, 'Submitted marketplace orders'),
        ('total_bookings', kpis['total_bookings']['value'], previous_bookings, 'Submitted facility bookings'),
        ('marketplace_revenue', current_sales, previous_sales, 'Completed-and-paid marketplace sales revenue'),
    )
    for key, current, previous, basis in rows:
        context = kpis[key]['secondary_text'] if key == 'total_users' or not current else ''
        kpis[key]['trend'] = activity_trend(current, previous, period, basis=basis, context=context)
