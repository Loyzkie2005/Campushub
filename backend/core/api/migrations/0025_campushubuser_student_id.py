from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0024_campushubuser_profile_onboarding"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE campushub_user "
                        "ADD COLUMN IF NOT EXISTS student_id varchar(50) NULL; "
                        "CREATE UNIQUE INDEX IF NOT EXISTS "
                        "campushub_user_student_id_unique "
                        "ON campushub_user (student_id) "
                        "WHERE student_id IS NOT NULL;"
                    ),
                    reverse_sql=(
                        "DROP INDEX IF EXISTS campushub_user_student_id_unique; "
                        "ALTER TABLE campushub_user "
                        "DROP COLUMN IF EXISTS student_id;"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="campushubuser",
                    name="student_id",
                    field=models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                        unique=True,
                    ),
                ),
            ],
        ),
    ]
