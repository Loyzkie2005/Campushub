from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from functools import wraps
from django.core.exceptions import PermissionDenied

from .models import Role, User


def admin_read_permissions(*codes):
    """Authorize a read endpoint without relaxing any write permission."""
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated or not any(request.user.has_perm(f"accounts.{code}") for code in codes):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorate


MARKETPLACE_RESTRICTED_SYSTEM_PERMISSIONS = frozenset({
    "can_export_marketplace_data",
    "can_export_facility_data",
    "can_system_backup",
    "can_restore_system_backup",
})

FACILITIES_RESTRICTED_SYSTEM_PERMISSIONS = frozenset({
    "can_export_facility_data",
    "can_export_marketplace_data",
    "can_system_backup",
    "can_restore_system_backup",
})


PERMISSION_MODULES = (
    (
        "Marketplace",
        (
            ("can_view_products", "View Products"),
            ("can_manage_products", "Manage Products"),
            ("can_approve_products", "Approve / Reject Products"),
            ("can_view_inventory", "View Inventory"),
            ("can_view_stock_movements", "View Stock Movements"),
            ("can_view_orders", "View Orders"),
            ("can_manage_orders", "Manage Orders"),
            ("can_view_sellers", "View Sellers"),
            ("can_manage_sellers", "Manage Sellers"),
        ),
    ),
    (
        "Facilities",
        (
            ("can_view_facilities", "View Facilities"),
            ("can_manage_facilities", "Manage Facilities"),
            ("can_view_bookings", "View Bookings"),
            ("can_manage_bookings", "Manage Bookings"),
            ("can_approve_bookings", "Approve / Reject Bookings"),
            ("can_manage_schedules", "Manage Calendar / Schedules"),
            ("can_record_facility_payment", "Record Payment / OR"),
        ),
    ),
    (
        "User Management",
        (
            ("can_view_users", "View Users"),
            ("can_reset_user_password", "Assist Account Recovery"),
            ("can_manage_admin_accounts", "Manage Admin Accounts"),
            ("can_manage_roles_permissions", "Manage Roles & Permissions"),
            ("can_view_user_monitoring", "View User Monitoring"),
        ),
    ),
    (
        "Reports",
        (
            ("can_view_marketplace_analytics", "View Marketplace Analytics"),
            ("can_view_facility_analytics", "View Facility Analytics"),
            ("can_view_marketplace_reports", "View Marketplace Reports"),
            ("can_view_facility_reports", "View Facility Reports"),
            ("can_view_reports", "View Reports"),
            ("can_generate_reports", "Generate / Export Reports"),
        ),
    ),
    (
        "System",
        (
            ("can_access_messages", "Messages"),
            ("can_access_notifications", "Notifications"),
            ("can_manage_settings", "Settings"),
            ("can_export_marketplace_data", "Export Marketplace Data"),
            ("can_export_facility_data", "Export Facility Data"),
            ("can_system_backup", "System Backup"),
            ("can_restore_system_backup", "Restore System Backup"),
        ),
    ),
)

ADMIN_UI_PERMISSION_CODENAMES = tuple(
    codename
    for _module_name, permissions in PERMISSION_MODULES
    for codename, _label in permissions
)
# Administrative actions require the corresponding read capability. This is
# shared by the editor and the existing setter; it never adds write authority.
PERMISSION_DEPENDENCIES = {
    "can_manage_products": ("can_view_products",),
    "can_approve_products": ("can_view_products",),
    "can_view_stock_movements": ("can_view_inventory",),
    "can_manage_orders": ("can_view_orders",),
    "can_manage_sellers": ("can_view_sellers",),
    "can_manage_facilities": ("can_view_facilities",),
    "can_manage_bookings": ("can_view_bookings",),
    "can_approve_bookings": ("can_view_bookings",),
    "can_manage_schedules": ("can_view_bookings",),
    "can_record_facility_payment": ("can_view_bookings",),
    "can_reset_user_password": ("can_view_users",),
    "can_view_user_monitoring": ("can_view_users",),
    "can_manage_admin_accounts": ("can_view_users",),
}


def include_permission_dependencies(codenames):
    """Add read prerequisites, retaining only existing permission definitions."""
    selected = set(codenames).intersection(ADMIN_UI_PERMISSION_CODENAMES)
    for code in tuple(selected):
        selected.update(PERMISSION_DEPENDENCIES.get(code, ()))
    return selected

# Retain buyer/mobile capabilities in the existing RBAC store, outside admin editing.
NORMAL_CAPABILITY_LABELS = {
    "can_browse_products": "Browse Products", "can_buy_products": "Buy Products",
    "can_browse_facilities": "Browse Facilities", "can_book_facilities": "Book Facilities",
}
ADMIN_PERMISSION_CODENAMES = ADMIN_UI_PERMISSION_CODENAMES + tuple(NORMAL_CAPABILITY_LABELS)
PERMISSION_LABELS = {
    codename: label
    for _module_name, permissions in PERMISSION_MODULES
    for codename, label in permissions
}
PERMISSION_LABELS.update(NORMAL_CAPABILITY_LABELS)
PERMISSION_CATEGORIES = {
    codename: module_name
    for module_name, permissions in PERMISSION_MODULES
    for codename, _label in permissions
}

# Browsing, buying, and booking are ordinary CampusHub capabilities. They do not
# grant access to the administration dashboard by themselves.
NORMAL_CAPABILITY_CODENAMES = frozenset(
    {
        "can_browse_products",
        "can_buy_products",
        "can_browse_facilities",
        "can_book_facilities",
    }
)
ADMIN_AUTHORITY_CODENAMES = tuple(
    codename
    for codename in ADMIN_PERMISSION_CODENAMES
    if codename not in NORMAL_CAPABILITY_CODENAMES
)

BUILTIN_ROLE_PERMISSIONS = {
    "Super Admin": ADMIN_PERMISSION_CODENAMES,
    "Marketplace Admin": (
        "can_view_products", "can_view_inventory", "can_view_stock_movements",
        "can_view_orders", "can_view_sellers",
        "can_view_users", "can_reset_user_password", "can_view_user_monitoring",
        "can_browse_products",
        "can_buy_products",
        "can_manage_products",
        "can_approve_products",
        "can_manage_orders",
        "can_manage_sellers",
        "can_view_marketplace_analytics",
        "can_view_marketplace_reports",
        "can_view_reports",
        "can_generate_reports",
        "can_access_messages",
        "can_access_notifications",
        "can_manage_settings",
    ),
    "Facilities Admin": (
        "can_view_facilities", "can_view_bookings",
        "can_browse_products",
        "can_buy_products",
        "can_browse_facilities",
        "can_book_facilities",
        "can_manage_facilities",
        "can_manage_bookings",
        "can_approve_bookings",
        "can_manage_schedules",
        "can_record_facility_payment",
        "can_view_facility_analytics",
        "can_view_facility_reports",
        "can_view_reports",
        "can_generate_reports",
        "can_access_messages",
        "can_access_notifications",
        "can_manage_settings",
    ),
    "User": (
        "can_browse_products",
        "can_buy_products",
        "can_browse_facilities",
        "can_book_facilities",
    ),
}


def _legacy_permissions_for_role_name(role_name: str) -> list[str]:
    return list(BUILTIN_ROLE_PERMISSIONS.get((role_name or "User").strip(), ()))


def get_role_record(role_name: str):
    name = (role_name or "").strip()
    if not name:
        return None
    return Role.objects.filter(role_name__iexact=name).first()


def role_scope_permissions(role_name):
    """Built-in administrators can be reduced within their domain, never expanded across it."""
    name = (role_name or "").strip().casefold()
    canonical = next((key for key in ("Marketplace Admin", "Facilities Admin") if key.casefold() == name), None)
    if canonical:
        return set(BUILTIN_ROLE_PERMISSIONS[canonical])
    return None  # Keep explicitly configured custom roles and Super Admin behavior.


def permissions_for_role(role_name: str) -> list[str]:
    if (role_name or "").strip().casefold() == "super admin":
        return list(ADMIN_PERMISSION_CODENAMES)

    role = get_role_record(role_name)
    if role is not None:
        if not role.is_active:
            return []
        granted = set(
            role.granted_permissions.filter(
                codename__in=ADMIN_PERMISSION_CODENAMES
            ).values_list("codename", flat=True)
        )
        if (role_name or "").strip().casefold() == "marketplace admin":
            granted.difference_update(MARKETPLACE_RESTRICTED_SYSTEM_PERMISSIONS)
        elif (role_name or "").strip().casefold() == "facilities admin":
            granted.difference_update(FACILITIES_RESTRICTED_SYSTEM_PERMISSIONS)
        scope = role_scope_permissions(role_name)
        if scope is not None:
            granted.intersection_update(scope)
        return [code for code in ADMIN_PERMISSION_CODENAMES if code in granted]
    return _legacy_permissions_for_role_name(role_name)


def permission_labels_for_role(role_name: str) -> list[str]:
    return [PERMISSION_LABELS[c] for c in permissions_for_role(role_name)]


def permission_set_label_for_role(role_name: str, codenames=None) -> str:
    normalized_role_name = (role_name or "").strip().casefold()
    if normalized_role_name == "super admin":
        return "Full Access"
    if normalized_role_name == "marketplace admin":
        return "Marketplace Access"
    if normalized_role_name == "facilities admin":
        return "Facilities Access"
    if normalized_role_name == "user":
        return "Base User Access"

    selected = set(codenames if codenames is not None else permissions_for_role(role_name))
    if selected == set(ADMIN_PERMISSION_CODENAMES):
        return "System Access"
    if not selected:
        return "No Access"
    domain_permissions = {
        "Marketplace": {
            "can_manage_products",
            "can_approve_products",
            "can_manage_orders",
            "can_manage_sellers",
            "can_view_marketplace_analytics",
            "can_view_marketplace_reports",
        },
        "Facilities": {
            "can_manage_facilities",
            "can_manage_bookings",
            "can_approve_bookings",
            "can_manage_schedules",
            "can_record_facility_payment",
            "can_view_facility_analytics",
            "can_view_facility_reports",
        },
        "User Management": {
            "can_view_users",
            "can_manage_admin_accounts",
            "can_manage_roles_permissions",
            "can_view_user_monitoring",
        },
    }
    active_domains = [
        module_name
        for module_name, permissions in domain_permissions.items()
        if selected.intersection(permissions)
    ]
    if len(active_domains) == 1:
        return f"{active_domains[0]} Access"
    if not active_domains and selected.issubset(NORMAL_CAPABILITY_CODENAMES):
        return "Standard Access"
    if not active_domains and selected.intersection({"can_view_reports", "can_generate_reports"}):
        return "Reports Access"
    if not active_domains and selected.intersection(
        {
            "can_access_messages",
            "can_access_notifications",
            "can_manage_settings",
            "can_export_marketplace_data",
            "can_export_facility_data",
            "can_system_backup",
            "can_restore_system_backup",
        }
    ):
        return "System Access"
    return "Custom Access"


def get_admin_permission_queryset():
    content_type = ContentType.objects.get_for_model(Role)
    return Permission.objects.filter(
        content_type=content_type,
        codename__in=ADMIN_PERMISSION_CODENAMES,
    )


def set_role_permissions(role: Role, codenames: list[str]) -> None:
    if (role.role_name or "").strip().casefold() == "super admin":
        valid = set(ADMIN_PERMISSION_CODENAMES)
    else:
        valid = set(codenames).intersection(ADMIN_PERMISSION_CODENAMES)
        if (role.role_name or "").strip().casefold() == "marketplace admin":
            valid.difference_update(MARKETPLACE_RESTRICTED_SYSTEM_PERMISSIONS)
        elif (role.role_name or "").strip().casefold() == "facilities admin":
            valid.difference_update(FACILITIES_RESTRICTED_SYSTEM_PERMISSIONS)
        scope = role_scope_permissions(role.role_name)
        if scope is not None:
            valid.intersection_update(scope)
        valid.update(include_permission_dependencies(valid))
    permissions = get_admin_permission_queryset().filter(codename__in=valid)
    role.granted_permissions.set(permissions)
    role.save(update_fields=["updated_at"])


def sync_users_for_role(role_name: str) -> None:
    for user in User.objects.filter(role=role_name):
        sync_user_admin_permissions(user)


def user_can_browse_products(user) -> bool:
    return user.has_perm("accounts.can_browse_products")


def user_can_buy_products(user) -> bool:
    return user.has_perm("accounts.can_buy_products")


def user_can_manage_products(user) -> bool:
    return user.has_perm("accounts.can_manage_products")


def user_can_manage_sellers(user) -> bool:
    return user.has_perm("accounts.can_manage_sellers")


def user_has_products_module_access(user) -> bool:
    return user_can_browse_products(user) or user_can_manage_products(user)


def user_can_browse_facilities(user) -> bool:
    return user.has_perm("accounts.can_browse_facilities")


def user_can_book_facilities(user) -> bool:
    return user.has_perm("accounts.can_book_facilities")


def user_can_manage_facilities(user) -> bool:
    return user.has_perm("accounts.can_manage_facilities")


def user_can_view_marketplace_analytics(user) -> bool:
    return user.has_perm("accounts.can_view_marketplace_analytics")


def user_can_view_facility_analytics(user) -> bool:
    return user.has_perm("accounts.can_view_facility_analytics")


def user_has_facility_module_access(user) -> bool:
    return user_can_browse_facilities(user) or user_can_manage_facilities(user) or user.has_perm("accounts.can_view_facilities")


def user_has_admin_access(user) -> bool:
    if not getattr(user, "is_active", False) or getattr(user, "is_suspended", False):
        return False
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    return any(
        user.has_perm(f"accounts.{codename}")
        for codename in ADMIN_AUTHORITY_CODENAMES
    )


def sync_user_admin_permissions(user) -> None:
    """Synchronize one administrator account from its database-backed role."""
    role_name = (user.role or "User").strip().lower()
    role_record = get_role_record(user.role)
    role_is_active = role_name == "super admin" or role_record is None or role_record.is_active
    should_be_superuser = role_is_active and role_name == "super admin"
    should_be_staff = role_is_active and role_name in {
        "super admin",
        "marketplace admin",
        "facilities admin",
    }

    access_fields = []
    if user.is_superuser != should_be_superuser:
        user.is_superuser = should_be_superuser
        access_fields.append("is_superuser")
    if user.is_staff != should_be_staff:
        user.is_staff = should_be_staff
        access_fields.append("is_staff")
    if access_fields:
        user.save(update_fields=access_fields)

    codenames = permissions_for_role(user.role)
    content_type = ContentType.objects.get_for_model(Role)
    permissions = Permission.objects.filter(
        content_type=content_type,
        codename__in=codenames,
    )
    user.user_permissions.set(permissions)


def get_admin_home_url(user) -> str:
    if user.is_superuser:
        return reverse("admin_dashboard_page")
    if user.has_perm("accounts.can_manage_products") or user.has_perm("accounts.can_view_products"):
        return reverse("admin_products_page")
    if user.has_perm("accounts.can_view_inventory") or user.has_perm("accounts.can_view_stock_movements"):
        return reverse("admin_products_page") + "?view=inventory"
    if user.has_perm("accounts.can_manage_orders") or user.has_perm("accounts.can_view_orders"):
        return reverse("admin_orders_page")
    if user.has_perm("accounts.can_manage_facilities") or user.has_perm("accounts.can_view_facilities"):
        return reverse("admin_facility_page")
    if user.has_perm("accounts.can_view_bookings") or user.has_perm("accounts.can_manage_bookings"):
        return reverse("admin_bookings_page")
    if user.has_perm("accounts.can_view_sellers") or user.has_perm("accounts.can_manage_sellers"):
        return reverse("admin_sellers_page")
    if user.has_perm("accounts.can_view_reports"):
        return reverse("admin_generate_reports_page")
    if user.has_perm("accounts.can_view_users"):
        return reverse("admin_users_page")
    if user.has_perm("accounts.can_access_messages"):
        return reverse("admin_messages_page")
    if user.has_perm("accounts.can_access_notifications"):
        return reverse("admin_notifications_page")
    return reverse("admin_login_page")
