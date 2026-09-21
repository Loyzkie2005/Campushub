from django.db import migrations


def remove_domain_backup_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")
    database = schema_editor.connection.alias
    permissions = list(Permission.objects.using(database).filter(
        content_type__app_label="accounts",
        content_type__model="role",
        codename__in=(
            "can_export_marketplace_data", "can_export_facility_data",
            "can_system_backup", "can_restore_system_backup", "can_backup_restore",
        ),
    ))
    for name in ("Marketplace Admin", "Facilities Admin"):
        for role in Role.objects.using(database).filter(role_name__iexact=name):
            role.granted_permissions.remove(*permissions)
        for user in User.objects.using(database).filter(role__iexact=name):
            user.user_permissions.remove(*permissions)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0022_role_scoped_data_export_permissions")]

    operations = [
        migrations.RunPython(remove_domain_backup_permissions, migrations.RunPython.noop),
    ]
