from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0026_campushubuser_access_control"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="facility",
                    name="location",
                    field=models.CharField(blank=True, default="", max_length=180),
                ),
                migrations.AddField(
                    model_name="facility",
                    name="workflow_config",
                    field=models.JSONField(blank=True, default=dict),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        (
                            "ALTER TABLE campushub_facility "
                            "ADD COLUMN IF NOT EXISTS location varchar(180) "
                            "NOT NULL DEFAULT '';"
                        ),
                        (
                            "ALTER TABLE campushub_facility "
                            "ADD COLUMN IF NOT EXISTS workflow_config jsonb "
                            "NOT NULL DEFAULT '{}'::jsonb;"
                        ),
                    ],
                    reverse_sql=[
                        "ALTER TABLE campushub_facility DROP COLUMN IF EXISTS workflow_config;",
                        "ALTER TABLE campushub_facility DROP COLUMN IF EXISTS location;",
                    ],
                ),
            ],
        ),
    ]
