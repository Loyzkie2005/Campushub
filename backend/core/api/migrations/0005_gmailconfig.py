# Gmail credentials stored in PostgreSQL

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_passwordresetcode_productinteraction"),
    ]

    operations = [
        migrations.CreateModel(
            name="GmailConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "gmail_user",
                    models.EmailField(
                        help_text="Gmail address that sends reset emails",
                        max_length=254,
                    ),
                ),
                (
                    "gmail_app_password",
                    models.CharField(
                        help_text="Google App Password (16 characters)",
                        max_length=128,
                    ),
                ),
                ("smtp_host", models.CharField(default="smtp.gmail.com", max_length=120)),
                ("smtp_port", models.PositiveIntegerField(default=587)),
                ("is_active", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Gmail configuration",
                "verbose_name_plural": "Gmail configurations",
            },
        ),
    ]
