from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0016_sync_builtin_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="contact_number",
            field=models.CharField(blank=True, default="", max_length=30),
        ),
        migrations.AddField(
            model_name="user",
            name="is_suspended",
            field=models.BooleanField(default=False),
        ),
    ]
