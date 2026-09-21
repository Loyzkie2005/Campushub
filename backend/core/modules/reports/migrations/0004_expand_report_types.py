from django.db import migrations, models


def update_legacy_report_types(apps, schema_editor):
    generated_report = apps.get_model("campushub_reports_module", "GeneratedReport")
    generated_report.objects.filter(report_type="users").update(report_type="user_accounts")
    generated_report.objects.filter(report_type="facilities").update(report_type="bookings")


def restore_legacy_report_types(apps, schema_editor):
    generated_report = apps.get_model("campushub_reports_module", "GeneratedReport")
    generated_report.objects.filter(report_type="user_accounts").update(report_type="users")
    generated_report.objects.filter(report_type="bookings").update(report_type="facilities")


class Migration(migrations.Migration):
    dependencies = [
        ("campushub_reports_module", "0003_remove_excel_report_format"),
    ]

    operations = [
        migrations.RunPython(update_legacy_report_types, restore_legacy_report_types),
        migrations.AlterField(
            model_name="generatedreport",
            name="report_type",
            field=models.CharField(
                choices=[
                    ("sales", "Sales Report"),
                    ("orders", "Orders Report"),
                    ("products", "Product & Inventory Report"),
                    ("low_stock", "Low Stock Report"),
                    ("bookings", "Facility Booking Report"),
                    ("facility_utilization", "Facility Utilization Report"),
                    ("facility_payments", "Facility Payments & OR Report"),
                    ("user_accounts", "User Accounts Report"),
                    ("user_activity", "User Login Activity Report"),
                ],
                max_length=24,
            ),
        ),
    ]
