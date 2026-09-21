from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0013_booking_facilityfeedback_facilitypayment"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="facility",
                    name="facility_type",
                    field=models.CharField(
                        blank=True,
                        choices=[
                            ("covered_court", "Covered Court"),
                            ("function_hall", "Function Hall"),
                            ("hostel", "Hostel"),
                            ("training_kitchen", "Training Kitchen"),
                            ("food_analysis", "Food Analysis Lab"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=40,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "DO $$ BEGIN "
                        "IF to_regclass('public.campushub_facility') IS NULL "
                        "AND to_regclass('public.api_facility') IS NOT NULL THEN "
                        "ALTER TABLE api_facility RENAME TO campushub_facility; "
                        "END IF; END $$; "
                        "ALTER TABLE campushub_facility "
                        "ADD COLUMN IF NOT EXISTS facility_type varchar(40) "
                        "NOT NULL DEFAULT 'other';"
                    ),
                    reverse_sql=(
                        "ALTER TABLE campushub_facility "
                        "DROP COLUMN IF EXISTS facility_type;"
                    ),
                ),
            ],
        ),
    ]
