from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0028_product_created_by"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="facility",
                    name="is_archived",
                    field=models.BooleanField(default=False),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        (
                            "ALTER TABLE campushub_facility "
                            "ADD COLUMN IF NOT EXISTS is_archived boolean "
                            "NOT NULL DEFAULT false;"
                        ),
                    ],
                    reverse_sql=[
                        "ALTER TABLE campushub_facility DROP COLUMN IF EXISTS is_archived;",
                    ],
                ),
            ],
        ),
    ]
