"""Permission-aware order querysets for marketplace administration and sellers."""

from api.models import MarketplaceOrder


def admin_order_queryset(user):
    """Return the shared marketplace order dataset to authorized administrators."""
    if not getattr(user, "is_authenticated", False):
        return MarketplaceOrder.objects.none()
    if user.is_superuser or user.has_perm("accounts.can_manage_orders"):
        return MarketplaceOrder.objects.all()
    return MarketplaceOrder.objects.none()


def seller_order_queryset(user):
    """Return only orders whose primary product belongs to the seller."""
    if not getattr(user, "is_authenticated", False):
        return MarketplaceOrder.objects.none()
    return MarketplaceOrder.objects.filter(product__seller=user)
