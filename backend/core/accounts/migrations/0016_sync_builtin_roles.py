from django.db import migrations


BUILTIN_ROLE_PERMISSIONS = {
    "Super Admin": (
        "can_access_products",
        "can_manage_products",
        "can_access_orders",
        "can_access_user_management",
        "can_access_facilities",
        "can_manage_facilities",
        "can_access_reports",
    ),
    "Marketplace Admin": (
        "can_access_products",
        "can_manage_products",
        "can_access_orders",
        "can_access_reports",
    ),
    "Facilities Admin": (
        "can_access_facilities",
        "can_manage_facilities",
        "can_access_reports",
    ),
    "User": (
        "can_access_products",
        "can_access_orders",
        "can_access_facilities",
    ),
}


def sync_builtin_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    content_type = ContentType.objects.get(app_label="accounts", model="role")
    permissions = {
        permission.codename: permission
        for permission in Permission.objects.filter(
            content_type=content_type,
            codename__in={
                codename
                for codenames in BUILTIN_ROLE_PERMISSIONS.values()
                for codename in codenames
            },
        )
    }

    # Correct the original typo before creating the canonical role record.
    misspelled = Role.objects.filter(role_name__iexact="Facilites Admin").first()
    canonical_facilities = Role.objects.filter(role_name__iexact="Facilities Admin").first()
    if misspelled is not None:
        User.objects.filter(role__iexact=misspelled.role_name).update(
            role="Facilities Admin"
        )
        if canonical_facilities is None:
            misspelled.role_name = "Facilities Admin"
            misspelled.save(update_fields=["role_name"])
        else:
            misspelled.delete()

    for role_name, codenames in BUILTIN_ROLE_PERMISSIONS.items():
        role, _ = Role.objects.get_or_create(
            role_name=role_name,
            defaults={"description": f"Built-in CampusHub {role_name} role."},
        )
        role.granted_permissions.set(
            [permissions[codename] for codename in codenames if codename in permissions]
        )

    # Ensure every legacy/custom role string has a corresponding Role row.
    for role_name in User.objects.exclude(role="").values_list("role", flat=True).distinct():
        Role.objects.get_or_create(
            role_name=role_name,
            defaults={"description": "CampusHub account role."},
        )

    for user in User.objects.filter(is_superuser=False):
        role = Role.objects.filter(role_name__iexact=user.role).first()
        if role is not None:
            user.user_permissions.set(role.granted_permissions.all())


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_split_product_permissions"),
    ]

    operations = [
        migrations.RunPython(sync_builtin_roles, migrations.RunPython.noop),
    ]
