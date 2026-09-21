from django.db import migrations


NEW_PERMISSIONS = (
    ("can_manage_sellers", "Can manage seller access"),
    ("can_view_marketplace_analytics", "Can view marketplace analytics"),
    ("can_view_facility_analytics", "Can view facility analytics"),
)

ROLE_GRANTS = {
    "Super Admin": tuple(codename for codename, _name in NEW_PERMISSIONS),
    "Marketplace Admin": (
        "can_manage_sellers",
        "can_view_marketplace_analytics",
    ),
    "Facilities Admin": ("can_view_facility_analytics",),
}


def add_domain_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")

    content_type = ContentType.objects.get(app_label="accounts", model="role")
    permissions = {}
    for codename, name in NEW_PERMISSIONS:
        permission, _created = Permission.objects.update_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )
        permissions[codename] = permission

    for role_name, codenames in ROLE_GRANTS.items():
        role = Role.objects.filter(role_name__iexact=role_name).first()
        selected = [permissions[codename] for codename in codenames]
        if role is not None:
            role.granted_permissions.add(*selected)
        for user in User.objects.filter(role__iexact=role_name):
            user.user_permissions.add(*selected)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0020_account_activity_and_session_presence"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="role",
            options={
                "ordering": ("role_name",),
                "permissions": [
                    ("can_browse_products", "Can browse products"),
                    ("can_buy_products", "Can buy products"),
                    ("can_manage_products", "Can manage products"),
                    ("can_approve_products", "Can approve products"),
                    ("can_manage_orders", "Can manage orders"),
                    ("can_manage_sellers", "Can manage seller access"),
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
                    ("can_view_marketplace_analytics", "Can view marketplace analytics"),
                    ("can_view_facility_analytics", "Can view facility analytics"),
                    ("can_view_reports", "Can view reports"),
                    ("can_generate_reports", "Can generate reports"),
                    ("can_access_messages", "Can access messages"),
                    ("can_access_notifications", "Can access notifications"),
                    ("can_manage_settings", "Can manage system settings"),
                    ("can_backup_restore", "Can back up and restore CampusHub data"),
                ],
                "verbose_name": "User Role",
                "verbose_name_plural": "User Roles",
            },
        ),
        migrations.RunPython(add_domain_permissions, migrations.RunPython.noop),
    ]
