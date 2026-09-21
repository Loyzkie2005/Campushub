from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("campushub_reports_module", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GeneratedReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_type", models.CharField(choices=[("sales", "Sales Report"), ("orders", "Order Report"), ("products", "Product Report"), ("users", "User Activity"), ("facilities", "Facility Usage")], max_length=24)),
                ("file_format", models.CharField(choices=[("csv", "CSV"), ("pdf", "PDF"), ("xlsx", "Excel")], max_length=8)),
                ("date_from", models.DateField(blank=True, null=True)),
                ("date_to", models.DateField(blank=True, null=True)),
                ("row_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("generated_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="generated_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "campushub_generated_report", "ordering": ("-created_at",)},
        ),
    ]
