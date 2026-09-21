from django.db import migrations, models


def seed_role_permissions(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    # Content types are normally finalized by post_migrate. A fresh database can
    # reach this data migration before the Role content type has been created.
    content_type, _ = ContentType.objects.get_or_create(
        app_label="accounts",
        model="role",
    )
    admin_codenames = (
        "can_access_products",
        "can_access_orders",
        "can_access_user_management",
        "can_access_facilities",
        "can_access_reports",
    )
    permission_map = {
        perm.codename: perm
        for perm in Permission.objects.filter(
            content_type=content_type,
            codename__in=admin_codenames,
        )
    }

    def legacy_codenames(role_name):
        role_lower = (role_name or "User").strip().lower()
        if role_lower in {"super admin", "superadmin"}:
            return list(admin_codenames)
        if "facility" in role_lower:
            return ["can_access_facilities"]
        if "marketplace" in role_lower or "seller" in role_lower:
            return ["can_access_products", "can_access_orders"]
        if role_lower == "user" or "student" in role_lower:
            return ["can_access_products", "can_access_orders"]
        return []

    for role in Role.objects.all():
        codenames = legacy_codenames(role.role_name)
        permissions = [
            permission_map[codename]
            for codename in codenames
            if codename in permission_map
        ]
        role.granted_permissions.set(permissions)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0012_admintabtoken"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="granted_permissions",
            field=models.ManyToManyField(
                blank=True,
                related_name="campushub_roles",
                to="auth.permission",
            ),
        ),
        migrations.RunPython(seed_role_permissions, migrations.RunPython.noop),
    ]
