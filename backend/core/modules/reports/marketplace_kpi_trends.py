"""Read-only comparisons for the dedicated Marketplace Admin overview cards."""
from django.db import DatabaseError, transaction
from django.db.models import Sum

from .dashboard_kpi_trends import activity_trend, comparison_dates


def marketplace_kpi_trends(orders, revenue_orders, period, *, current_orders, current_revenue, available=True):
    """Compare canonical scoped querysets; do not substitute completed-order counts.

    Missing comparisons produce no trend, never an invented zero baseline. The
    savepoint keeps a failed optional comparison from breaking later page reads.
    """
    result = {'orders': None, 'revenue': None, 'available': False}
    if not available:
        return result
    previous_start, previous_end = comparison_dates(period)
    try:
        with transaction.atomic():
            previous_orders = orders.filter(created_at__date__range=(previous_start, previous_end)).count()
            previous_revenue = revenue_orders.filter(analytics_at__date__range=(previous_start, previous_end)).aggregate(
                amount=Sum('total_price'))['amount'] or 0
    except DatabaseError:
        return result
    orders_trend = activity_trend(current_orders, previous_orders, period,
        basis='Submitted marketplace orders', context='All existing authorized order statuses are included.')
    if current_orders > 0 and previous_orders == 0:
        orders_trend['label'] = '\u2197 New Orders'
    result.update(orders=orders_trend, available=True)
    # A zero revenue denominator cannot support a percentage comparison.
    if previous_revenue > 0:
        result['revenue'] = activity_trend(current_revenue, previous_revenue, period,
            basis='Completed-and-paid marketplace revenue', context='Uses the existing revenue recognition timestamp.')
    return result
