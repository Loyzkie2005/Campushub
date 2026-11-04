"""Shared web/mobile account populations, counted as records rather than inferred people."""
from django.db.models import Count, Exists, OuterRef, Q
from accounts.models import User
from api.models import CampusHubUser, SellerRequest
from modules.marketplace.services.reporting_metrics import approved_seller_request_filter


def account_population(period, *, include_sellers=False, previous_range=None):
    """Two aggregates feed Dashboard snapshots and Users Analytics with identical definitions."""
    dates = (period.start, period.end)
    def fields(owner, created):
        result = {'total': Count('pk'), 'new': Count('pk', filter=Q(**{created + '__date__range': dates})),
                  'active': Count('pk', filter=Q(is_active=True, is_suspended=False))}
        if previous_range is not None:
            result['previous_new'] = Count('pk', filter=Q(**{created + '__date__range': previous_range}))
        if include_sellers:
            requests = SellerRequest.objects.filter(approved_seller_request_filter(owner), **{owner + '_id': OuterRef('pk')})
            eligible = Q(Exists(requests))
            if owner == 'user':
                suspended = SellerRequest.objects.filter(user_id=OuterRef('pk'), is_suspended=True)
                eligible |= Q(role__iexact='Seller', is_active=True, is_suspended=False) & ~Q(Exists(suspended))
            result.update(sellers=Count('pk', filter=eligible),
                seller_approved_in_period=Count('pk', filter=Exists(requests.filter(reviewed_at__date__range=dates))),
                sellers_dated=Count('pk', filter=Exists(requests.filter(reviewed_at__isnull=False))))
        return result
    web = User.objects.aggregate(**fields('user', 'date_joined'))
    mobile = CampusHubUser.objects.aggregate(**fields('mobile_user', 'created_at'),
        students=Count('pk', filter=Q(user_type=CampusHubUser.USER_TYPE_STUDENT)),
        faculty=Count('pk', filter=Q(user_type=CampusHubUser.USER_TYPE_FACULTY)),
        guests=Count('pk', filter=Q(user_type=CampusHubUser.USER_TYPE_GUEST)))
    return {'web': web, 'mobile': mobile}
