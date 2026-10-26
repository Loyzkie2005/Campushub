"""Global administrators have no academic permission scope; retain student affiliations."""
from django.db import migrations
from django.db.models import Q


def clear_global_scope(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.using(schema_editor.connection.alias).filter(
        Q(is_superuser=True) | Q(role__iexact='Super Admin') | Q(role__iexact='Facilities Admin')
    ).update(department=None, major=None)


class Migration(migrations.Migration):
    dependencies = [('accounts', '0024_program_major_structure')]
    operations = [migrations.RunPython(clear_global_scope, migrations.RunPython.noop)]
