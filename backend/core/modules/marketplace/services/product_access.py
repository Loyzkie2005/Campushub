"""Permission-aware product querysets shared by marketplace admin surfaces."""

from api.models import Product


def user_can_administer_products(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    return bool(
        user.is_superuser
        or user.has_perm("accounts.can_manage_products")
        or user.has_perm("accounts.can_approve_products")
    )


def admin_product_queryset(user):
    """Return the shared marketplace dataset to authorized administrators."""
    if not user_can_administer_products(user):
        return Product.objects.none()
    return Product.objects.all()


def image_visible_product_queryset(user):
    """Expose all images to product admins and approved listing images publicly."""
    if user_can_administer_products(user):
        return Product.objects.all()
    return Product.objects.filter(
        approval_status=Product.STATUS_APPROVED,
        is_archived=False,
    )
