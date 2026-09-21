from django.db import migrations, models


ADMIN_CODENAMES = (
    "can_access_products",
    "can_manage_products",
    "can_access_orders",
    "can_access_user_management",
    "can_access_facilities",
    "can_manage_facilities",
    "can_access_reports",
)


def split_product_permissions(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    content_type = ContentType.objects.get(app_label="accounts", model="role")
    permission_map = {
        perm.codename: perm
        for perm in Permission.objects.filter(
            content_type=content_type,
            codename__in=ADMIN_CODENAMES,
        )
    }

    buy_perm = permission_map.get("can_access_products")
    manage_perm = permission_map.get("can_manage_products")
    if buy_perm:
        buy_perm.name = "Can buy products"
        buy_perm.save(update_fields=["name"])

    for role in Role.objects.all().prefetch_related("granted_permissions"):
        role_lower = role.role_name.lower()
        current = set(role.granted_permissions.values_list("codename", flat=True))

        if role_lower in {"super admin", "superadmin"} and manage_perm:
            role.granted_permissions.add(manage_perm)
            current.add("can_manage_products")
        elif role_lower in {"user", "student"} or "marketplace" in role_lower or "seller" in role_lower:
            if manage_perm:
                role.granted_permissions.remove(manage_perm)
            current.discard("can_manage_products")
            if buy_perm:
                role.granted_permissions.add(buy_perm)
                current.add("can_access_products")

        codenames = [code for code in ADMIN_CODENAMES if code in current]
        permissions = [
            permission_map[code] for code in codenames if code in permission_map
        ]

        for user in User.objects.filter(role=role.role_name):
            if user.is_superuser:
                continue
            user.user_permissions.set(permissions)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0014_split_facility_permissions"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="role",
            options={
                "ordering": ("role_name",),
                "permissions": [
                    ("can_access_products", "Can buy products"),
                    ("can_manage_products", "Can manage products"),
                    ("can_access_orders", "Can access Orders"),
                    (
                        "can_access_user_management",
                        "Can access User Management",
                    ),
                    ("can_access_facilities", "Can book facilities"),
                    ("can_manage_facilities", "Can manage facilities"),
                    ("can_access_reports", "Can access Reports"),
                ],
                "verbose_name": "User Role",
                "verbose_name_plural": "User Roles",
            },
        ),
        migrations.RunPython(split_product_permissions, migrations.RunPython.noop),
    ]
