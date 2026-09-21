from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0018_rename_mobile_username_to_student_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "DO $$ BEGIN "
                        "IF to_regclass('public.campushub_user') IS NOT NULL THEN "
                        "ALTER TABLE campushub_user ADD COLUMN IF NOT EXISTS "
                        "last_login timestamp with time zone NULL; "
                        "END IF; END $$;"
                    ),
                    reverse_sql=(
                        "DO $$ BEGIN "
                        "IF to_regclass('public.campushub_user') IS NOT NULL THEN "
                        "ALTER TABLE campushub_user DROP COLUMN IF EXISTS last_login; "
                        "END IF; END $$;"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="campushubuser",
                    name="last_login",
                    field=models.DateTimeField(blank=True, null=True),
                ),
            ],
        ),
    ]
