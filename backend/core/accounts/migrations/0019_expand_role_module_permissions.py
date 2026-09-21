from django.db import migrations


PERMISSION_DEFINITIONS = (
    ("can_browse_products", "Can browse products"),
    ("can_buy_products", "Can buy products"),
    ("can_manage_products", "Can manage products"),
    ("can_approve_products", "Can approve products"),
    ("can_manage_orders", "Can manage orders"),
    ("can_view_marketplace_reports", "Can view marketplace reports"),
    ("can_browse_facilities", "Can browse facilities"),
    ("can_book_facilities", "Can book facilities"),
    ("can_manage_facilities", "Can manage facilities"),
    ("can_manage_bookings", "Can manage facility bookings"),
    ("can_approve_bookings", "Can approve or reject facility bookings"),
    ("can_manage_schedules", "Can manage facility calendars and schedules"),
    ("can_record_facility_payment", "Can record facility payments and official receipts"),
    ("can_view_facility_reports", "Can view facility reports"),
    ("can_view_users", "Can view users"),
    ("can_manage_admin_accounts", "Can manage administrator accounts"),
    ("can_manage_roles_permissions", "Can manage roles and permissions"),
    ("can_view_user_monitoring", "Can view user monitoring"),
    ("can_view_reports", "Can view reports"),
    ("can_generate_reports", "Can generate reports"),
    ("can_access_messages", "Can access messages"),
    ("can_access_notifications", "Can access notifications"),
    ("can_manage_settings", "Can manage system settings"),
    ("can_backup_restore", "Can back up and restore CampusHub data"),
)

ALL_CODENAMES = tuple(codename for codename, _name in PERMISSION_DEFINITIONS)
BUILTIN_ROLE_PERMISSIONS = {
    "Super Admin": ALL_CODENAMES,
    "Marketplace Admin": (
        "can_browse_products",
        "can_buy_products",
        "can_manage_products",
        "can_approve_products",
        "can_manage_orders",
        "can_view_marketplace_reports",
        "can_view_reports",
        "can_generate_reports",
        "can_access_messages",
        "can_access_notifications",
    ),
    "Facilities Admin": (
        "can_browse_products",
        "can_buy_products",
        "can_browse_facilities",
        "can_book_facilities",
        "can_manage_facilities",
        "can_manage_bookings",
        "can_approve_bookings",
        "can_manage_schedules",
        "can_record_facility_payment",
        "can_view_facility_reports",
        "can_view_reports",
        "can_generate_reports",
        "can_access_messages",
        "can_access_notifications",
    ),
    "User": (
        "can_browse_products",
        "can_buy_products",
        "can_browse_facilities",
        "can_book_facilities",
    ),
}
LEGACY_PERMISSION_MAP = {
    "can_access_products": ("can_browse_products", "can_buy_products"),
    "can_manage_products": ("can_manage_products",),
    "can_access_orders": ("can_manage_orders",),
    "can_access_user_management": (
        "can_view_users",
        "can_manage_admin_accounts",
        "can_manage_roles_permissions",
        "can_view_user_monitoring",
    ),
    "can_access_facilities": ("can_browse_facilities", "can_book_facilities"),
    "can_manage_facilities": (
        "can_manage_facilities",
        "can_manage_bookings",
        "can_approve_bookings",
        "can_manage_schedules",
        "can_record_facility_payment",
    ),
    "can_access_reports": (
        "can_view_marketplace_reports",
        "can_view_facility_reports",
        "can_view_reports",
        "can_generate_reports",
    ),
}


def expand_permissions(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    content_type = ContentType.objects.get(app_label="accounts", model="role")
    permission_map = {}
    for codename, name in PERMISSION_DEFINITIONS:
        permission, _ = Permission.objects.update_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )
        permission_map[codename] = permission

    for role in Role.objects.all().prefetch_related("granted_permissions"):
        if role.role_name in BUILTIN_ROLE_PERMISSIONS:
            selected = set(BUILTIN_ROLE_PERMISSIONS[role.role_name])
        else:
            previous = set(role.granted_permissions.values_list("codename", flat=True))
            selected = set(previous).intersection(ALL_CODENAMES)
            for old_codename, replacements in LEGACY_PERMISSION_MAP.items():
                if old_codename in previous:
                    selected.update(replacements)
        role.granted_permissions.set(
            [permission_map[codename] for codename in ALL_CODENAMES if codename in selected]
        )

    for user in User.objects.filter(is_superuser=False):
        role = Role.objects.filter(role_name__iexact=user.role).first()
        if role is not None and role.is_active:
            user.user_permissions.set(role.granted_permissions.all())
        else:
            user.user_permissions.clear()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0018_role_is_active"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="role",
            options={
                "ordering": ("role_name",),
                "permissions": list(PERMISSION_DEFINITIONS),
                "verbose_name": "User Role",
                "verbose_name_plural": "User Roles",
            },
        ),
        migrations.RunPython(expand_permissions, migrations.RunPython.noop),
    ]
