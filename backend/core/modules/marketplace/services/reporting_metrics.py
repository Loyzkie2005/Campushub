"""Shared read-only marketplace metric definitions; never grant seller permissions."""
from decimal import Decimal


def average_order_value(revenue, qualifying_orders):
    """A zero-value qualifying sale is real; a missing order denominator is undefined."""
    return Decimal(revenue or 0) / qualifying_orders if qualifying_orders else None


def approved_seller_request_filter(owner):
    """Approval/access evidence shared by web/mobile reporting; account type stays independent."""
    from django.db.models import Q
    return Q(status='approved', is_suspended=False, **{
        owner + '__isnull': False, owner + '__is_active': True, owner + '__is_suspended': False})


def seller_access_snapshot(period, *, population=None):
    """Current web/mobile access, keeping the Dashboard's legacy enabled Seller fallback."""
    from modules.reports.account_metrics import account_population
    population = population if population is not None else account_population(period, include_sellers=True)
    return {'total': sum(row['sellers'] for row in population.values()),
            'approved_in_period': sum(row['seller_approved_in_period'] for row in population.values()),
            'with_recorded_approval': sum(row['sellers_dated'] for row in population.values())}
