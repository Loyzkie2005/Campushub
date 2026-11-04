"""Actual account ownership; mobile and Django IDs are different namespaces."""
from django.http import JsonResponse
from api.models import CampusHubUser


class SelfProductInteraction(ValueError):
    pass


def owns_product(actor, product):
    if actor is None or not getattr(actor, 'pk', None):
        return False
    if isinstance(actor, CampusHubUser):
        return product.mobile_seller_id == actor.pk
    return bool(getattr(actor, 'is_authenticated', False) and product.seller_id == actor.pk)


def authenticated_actor(request):
    if request.headers.get('Authorization'):
        from api.views import _mobile_user_from_bearer
        return _mobile_user_from_bearer(request)
    actor = getattr(request, 'user', None)
    if actor is not None and actor.is_authenticated and actor.is_active and not getattr(actor, 'is_suspended', False):
        return actor, None
    return None, JsonResponse({'error': 'Sign in to interact with products.'}, status=401)


def require_other_owner(actor, product):
    if owns_product(actor, product):
        raise SelfProductInteraction('You cannot purchase, cart or favorite your own product.')
