from django.db import migrations, models


def add_year_section(apps, schema_editor):
    """Extend the existing unmanaged mobile table; never replace account records."""
    model = apps.get_model('api', 'CampusHubUser')
    connection = schema_editor.connection
    if model._meta.db_table not in connection.introspection.table_names():
        return  # Isolated tests create the unmanaged table from the current model.
    with connection.cursor() as cursor:
        columns = {column.name for column in connection.introspection.get_table_description(cursor, model._meta.db_table)}
    if 'year_section' not in columns:
        schema_editor.add_field(model, model._meta.get_field('year_section'))


class Migration(migrations.Migration):
    dependencies = [('api', '0039_seller_owner_constraints')]
    operations = [
        migrations.AddField(model_name='campushubuser', name='year_section',
                            field=models.CharField(blank=True, default='', max_length=120)),
        # Match the existing unmanaged-table migration pattern. Reverse preserves data.
        migrations.RunPython(add_year_section, migrations.RunPython.noop),
    ]
