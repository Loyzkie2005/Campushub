from django.db import migrations, models


def add_profile_photo(apps, schema_editor):
    """The mobile user table is unmanaged; add only the missing photo column."""
    model = apps.get_model("api", "CampusHubUser")
    connection = schema_editor.connection
    if model._meta.db_table not in connection.introspection.table_names():
        return
    with connection.cursor() as cursor:
        columns = {column.name for column in connection.introspection.get_table_description(cursor, model._meta.db_table)}
    if "profile_photo" not in columns:
        schema_editor.add_field(model, model._meta.get_field("profile_photo"))


class Migration(migrations.Migration):
    dependencies = [("api", "0041_seller_bundle_suggestions")]
    operations = [
        migrations.AddField(
            model_name="campushubuser", name="profile_photo",
            field=models.ImageField(upload_to="profile-photos/", max_length=255, blank=True, default=""),
        ),
        migrations.RunPython(add_profile_photo, migrations.RunPython.noop),
    ]
