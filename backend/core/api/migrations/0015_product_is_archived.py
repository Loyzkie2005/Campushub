from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0014_facility_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="is_archived",
            field=models.BooleanField(default=False),
        ),
    ]
