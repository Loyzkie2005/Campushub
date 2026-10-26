"""Permission-aware order querysets for marketplace administration and sellers."""

from api.models import CampusHubUser, MarketplaceOrder


def scoped_marketplace_orders(user):
    """Shared resource boundary for Orders, Dashboard and Analytics; no buyer filter."""
    from accounts.academic import scope_products
    orders = scope_products(MarketplaceOrder.objects.all(), user, prefix="product__")
    if not user.is_superuser:
        orders = orders.exclude(customization__items__1__isnull=False)
    return orders


def admin_order_queryset(user):
    """Return the shared marketplace order dataset to authorized administrators."""
    if not getattr(user, "is_authenticated", False):
        return MarketplaceOrder.objects.none()
    if user.is_superuser or user.has_perm("accounts.can_manage_orders") or user.has_perm("accounts.can_view_orders"):
        return scoped_marketplace_orders(user)
    return MarketplaceOrder.objects.none()


def seller_order_queryset(user):
    """Return only orders whose primary product belongs to the seller."""
    if isinstance(user, CampusHubUser):
        if not user.is_active or user.is_suspended:
            return MarketplaceOrder.objects.none()
        return MarketplaceOrder.objects.filter(product__mobile_seller=user).exclude(customization__items__1__isnull=False)
    if not getattr(user, "is_authenticated", False):
        return MarketplaceOrder.objects.none()
    return MarketplaceOrder.objects.filter(product__seller=user)
