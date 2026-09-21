from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0017_user_access_metadata"),
        ("api", "0025_campushubuser_student_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE campushub_user ADD COLUMN IF NOT EXISTS role varchar(100) NOT NULL DEFAULT 'User';",
                        "ALTER TABLE campushub_user ADD COLUMN IF NOT EXISTS department_id bigint NULL;",
                        "ALTER TABLE campushub_user ADD COLUMN IF NOT EXISTS is_active boolean NOT NULL DEFAULT true;",
                        "ALTER TABLE campushub_user ADD COLUMN IF NOT EXISTS is_suspended boolean NOT NULL DEFAULT false;",
                        "CREATE INDEX IF NOT EXISTS campushub_user_department_id_idx ON campushub_user (department_id);",
                    ],
                    reverse_sql=[
                        "DROP INDEX IF EXISTS campushub_user_department_id_idx;",
                        "ALTER TABLE campushub_user DROP COLUMN IF EXISTS is_suspended;",
                        "ALTER TABLE campushub_user DROP COLUMN IF EXISTS is_active;",
                        "ALTER TABLE campushub_user DROP COLUMN IF EXISTS department_id;",
                        "ALTER TABLE campushub_user DROP COLUMN IF EXISTS role;",
                    ],
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="campushubuser",
                    name="role",
                    field=models.CharField(blank=True, default="User", max_length=100),
                ),
                migrations.AddField(
                    model_name="campushubuser",
                    name="department",
                    field=models.ForeignKey(
                        blank=True,
                        db_column="department_id",
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="mobile_users",
                        to="accounts.department",
                    ),
                ),
                migrations.AddField(
                    model_name="campushubuser",
                    name="is_active",
                    field=models.BooleanField(default=True),
                ),
                migrations.AddField(
                    model_name="campushubuser",
                    name="is_suspended",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
