from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_user_access_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="role",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
