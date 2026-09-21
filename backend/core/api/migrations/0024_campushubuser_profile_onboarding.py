from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0023_marketplaceorder_message_to_seller"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "CREATE TABLE IF NOT EXISTS campushub_user ("
                        "id bigserial PRIMARY KEY, "
                        "first_name varchar(100) NOT NULL, "
                        "last_name varchar(100) NOT NULL, "
                        "username varchar(50) NOT NULL UNIQUE, "
                        "email varchar(150) NOT NULL UNIQUE, "
                        "password_hash text NOT NULL, "
                        "last_login timestamp with time zone NULL, "
                        "created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP, "
                        "updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP"
                        "); "
                        "ALTER TABLE campushub_user "
                        "ADD COLUMN IF NOT EXISTS user_type varchar(20) NOT NULL DEFAULT '', "
                        "ADD COLUMN IF NOT EXISTS institutional_id varchar(50) NOT NULL DEFAULT '', "
                        "ADD COLUMN IF NOT EXISTS contact_number varchar(30) NOT NULL DEFAULT '', "
                        "ADD COLUMN IF NOT EXISTS profile_completed boolean NOT NULL DEFAULT false; "
                        "UPDATE campushub_user SET profile_completed = true "
                        "WHERE user_type = '' AND institutional_id = '' AND contact_number = '';"
                    ),
                    reverse_sql=(
                        "ALTER TABLE campushub_user "
                        "DROP COLUMN IF EXISTS profile_completed, "
                        "DROP COLUMN IF EXISTS contact_number, "
                        "DROP COLUMN IF EXISTS institutional_id, "
                        "DROP COLUMN IF EXISTS user_type;"
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="campushubuser",
                    name="user_type",
                    field=models.CharField(
                        blank=True,
                        choices=[
                            ("student", "Student"),
                            ("faculty", "Faculty"),
                            ("guest", "Guest"),
                        ],
                        default="",
                        max_length=20,
                    ),
                ),
                migrations.AddField(
                    model_name="campushubuser",
                    name="institutional_id",
                    field=models.CharField(blank=True, default="", max_length=50),
                ),
                migrations.AddField(
                    model_name="campushubuser",
                    name="contact_number",
                    field=models.CharField(blank=True, default="", max_length=30),
                ),
                migrations.AddField(
                    model_name="campushubuser",
                    name="profile_completed",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
