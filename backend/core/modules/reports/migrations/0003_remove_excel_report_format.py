from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("campushub_reports_module", "0002_generatedreport"),
    ]

    operations = [
        migrations.AlterField(
            model_name="generatedreport",
            name="file_format",
            field=models.CharField(
                choices=[("csv", "CSV"), ("pdf", "PDF")],
                max_length=8,
            ),
        ),
    ]
