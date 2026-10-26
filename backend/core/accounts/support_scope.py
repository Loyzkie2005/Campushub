"""One backend boundary for marketplace account support and activity reads."""
from django.db.models import Q

from .academic import scope_users
from .models import User


def is_super_admin(actor):
    return actor.is_superuser or (actor.role or "").strip().casefold() == "super admin"


def is_marketplace_admin(actor):
    return not is_super_admin(actor) and (actor.role or "").strip().casefold() == "marketplace admin"


def support_accounts(queryset, actor, *, mobile=False):
    if not is_marketplace_admin(actor):
        return queryset
    # Ordinary users only. Custom/system administrators are not support targets.
    queryset = scope_users(queryset, actor).filter(role__iexact="User")
    if mobile:
        return queryset.exclude(user_type__iexact="admin")
    from .role_permissions import ADMIN_AUTHORITY_CODENAMES
    return queryset.filter(is_staff=False, is_superuser=False).exclude(
        user_permissions__codename__in=ADMIN_AUTHORITY_CODENAMES).exclude(
        groups__permissions__codename__in=ADMIN_AUTHORITY_CODENAMES).distinct()


def is_administrator_account(source, account, *, has_admin_authority=None):
    """Classify stored identity/access, never the table's display label.

    User is the existing ordinary role; all custom/non-User roles fail closed.
    The optional authority flag comes from the Users page's batched DB query.
    """
    if source not in {"admin", "mobile"} or account is None:
        return True
    if ((account.role or "").strip().casefold() != "user"
            or getattr(account, "is_staff", False) or getattr(account, "is_superuser", False)
            or (getattr(account, "user_type", "") or "").strip().casefold() == "admin"):
        return True
    if source == "mobile":
        return (account.user_type or "").strip().casefold() not in {"", "student", "faculty", "guest"}
    if has_admin_authority is None:
        from .role_permissions import ADMIN_AUTHORITY_CODENAMES
        has_admin_authority = User.objects.filter(pk=account.pk).filter(
            Q(user_permissions__codename__in=ADMIN_AUTHORITY_CODENAMES)
            | Q(groups__permissions__codename__in=ADMIN_AUTHORITY_CODENAMES)).exists()
    return bool(has_admin_authority)


def can_assist_recovery_actor(actor):
    if not actor.has_perm("accounts.can_reset_user_password"):
        return False
    # Facilities Admin remains excluded even if an old/direct grant exists.
    return is_super_admin(actor) or (actor.role or "").strip().casefold() != "facilities admin"


def can_view_recovery_info(actor, source, account, *, has_admin_authority=None):
    """Authorize assistance information; this does not authorize code/password changes."""
    if not can_assist_recovery_actor(actor) or is_administrator_account(
            source, account, has_admin_authority=has_admin_authority):
        return False
    if is_super_admin(actor):
        return True
    if is_marketplace_admin(actor):
        from .academic import has_valid_marketplace_scope
        # Same scope rule as scope_users, using the already-loaded foreign keys.
        return bool(has_valid_marketplace_scope(actor)
            and account.department_id == actor.department_id
            and (not actor.major_id or account.major_id == actor.major_id))
    return source == "mobile" or not getattr(account, "is_staff", False)


def can_manage_account(actor, account):
    from .user_management import is_admin_role
    return bool(actor.has_perm("accounts.can_manage_admin_accounts") and not is_marketplace_admin(actor)
        and (is_super_admin(actor) or (not is_admin_role(account.role)
            and not getattr(account, "is_staff", False) and not getattr(account, "is_superuser", False))))


def can_manage_seller(actor, source, account):
    if source != "mobile" or is_administrator_account(source, account):
        return False
    if not (actor.has_perm("accounts.can_manage_sellers") or is_super_admin(actor) and actor.has_perm("accounts.can_manage_admin_accounts")):
        return False
    if is_marketplace_admin(actor):
        from api.models import CampusHubUser
        return support_accounts(CampusHubUser.objects.filter(pk=account.pk), actor, mobile=True).exists()
    return is_super_admin(actor)


MARKETPLACE_MODULES = ("Marketplace", "Products", "Inventory", "Orders", "Sellers")
SUPPORT_EVENTS = ("SELLER_APPROVED", "SELLER_REJECTED", "SELLER_PENDING", "SELLER_SUSPENDED",
                  "SELLER_RESTORED", "PASSWORD_RESET_REQUESTED", "ACCOUNT_RECOVERY_INITIATED",
                  "ACCOUNT_RECOVERY_CODE_SENT", "EMAIL_VERIFICATION_CODE_SENT", "USERNAME_RECOVERY_INITIATED", "PASSWORD_RESET_INITIATED", "EMAIL_VERIFICATION_INITIATED",
                  "ACCOUNT_DEACTIVATED", "ACCOUNT_REACTIVATED")


def support_activity(queryset, actor):
    if not is_marketplace_admin(actor):
        return queryset
    from api.models import CampusHubUser
    django_refs = support_accounts(User.objects.all(), actor).values_list("pk", flat=True)
    mobile_refs = support_accounts(CampusHubUser.objects.all(), actor, mobile=True).values_list("pk", flat=True)
    # Restrict before pagination, serialization, totals, latest-event and history queries.
    refs = [f"admin:{pk}" for pk in django_refs] + [f"mobile:{pk}" for pk in mobile_refs]
    queryset = queryset.filter(Q(metadata__program_id__isnull=True) | Q(metadata__program_id=actor.department_id))
    if actor.major_id:
        queryset = queryset.filter(Q(metadata__major_id__isnull=True) | Q(metadata__major_id=actor.major_id))
    return queryset.filter(account_ref__in=refs).filter(
        Q(module__in=MARKETPLACE_MODULES) | Q(module="User Management", activity_type__in=SUPPORT_EVENTS))


def scope_marketplace_activity(queryset, actor):
    """Resource-based audit reads; customer affiliation is not order ownership.

    Reuse Products/Orders/Sellers boundaries and fail closed on missing or
    conflicting evidence. Does not broaden User Monitoring's support scope.
    """
    from django.db.models import CharField, Value
    from django.db.models.functions import Cast, Concat
    from django.db.models.fields.json import KeyTextTransform
    from .academic import has_valid_marketplace_scope, scope_products, scope_seller_requests, unrestricted_marketplace
    from api.models import Product, SellerRequest
    from modules.marketplace.services.order_access import admin_order_queryset

    marketplace_events = Q(module__in=(*MARKETPLACE_MODULES, "Marketplace Orders")) | Q(
        module="User Management", activity_type__istartswith="SELLER_")
    event_types = Q(activity_type__istartswith="PRODUCT_") | Q(activity_type__istartswith="INVENTORY_") | Q(
        activity_type__istartswith="ORDER_") | Q(activity_type__istartswith="SELLER_")
    queryset = queryset.filter(marketplace_events & event_types)
    if unrestricted_marketplace(actor):
        return queryset
    if not has_valid_marketplace_scope(actor):
        return queryset.none()

    def text_ids(rows):
        return rows.annotate(_audit_id=Cast("pk", CharField())).values("_audit_id")

    products = text_ids(scope_products(Product.objects.all(), actor))
    orders = text_ids(admin_order_queryset(actor))
    applications = text_ids(scope_seller_requests(SellerRequest.objects.all(), actor))
    queryset = queryset.annotate(**{f"_audit_{name}": KeyTextTransform(name + "_id", "metadata")
                                  for name in ("product", "order", "seller_request", "program", "major")})
    # The most specific reference takes precedence, preventing account fallbacks
    # from revealing an out-of-scope resource belonging to an in-scope seller.
    evidence = Q(_audit_order__in=orders) | Q(_audit_order__isnull=True, _audit_product__in=products) | Q(
        _audit_order__isnull=True, _audit_product__isnull=True, _audit_seller_request__in=applications)
    from api.models import CampusHubUser
    refs = scope_users(User.objects.filter(is_staff=False, is_superuser=False), actor).annotate(
        _audit_ref=Concat(Value("admin:"), Cast("pk", CharField()))).values("_audit_ref")
    mobile_refs = scope_users(CampusHubUser.objects.exclude(user_type__iexact="admin"), actor).annotate(
        _audit_ref=Concat(Value("mobile:"), Cast("pk", CharField()))).values("_audit_ref")
    evidence |= Q(_audit_order__isnull=True, _audit_product__isnull=True, _audit_seller_request__isnull=True,
                  activity_type__istartswith="SELLER_") & (Q(account_ref__in=refs) | Q(account_ref__in=mobile_refs))
    queryset = queryset.filter(evidence).filter(Q(_audit_program__isnull=True) | Q(_audit_program=str(actor.department_id)))
    if actor.major_id:
        queryset = queryset.filter(Q(_audit_major__isnull=True) | Q(_audit_major=str(actor.major_id)))
    return queryset
