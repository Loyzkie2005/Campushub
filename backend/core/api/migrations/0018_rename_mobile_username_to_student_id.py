from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0017_marketplaceorder_order_code_2026"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "DO $$ BEGIN "
                        "IF to_regclass('public.campushub_user') IS NOT NULL "
                        "AND EXISTS (SELECT 1 FROM information_schema.columns "
                        "WHERE table_schema = 'public' AND table_name = 'campushub_user' "
                        "AND column_name = 'username') "
                        "AND NOT EXISTS (SELECT 1 FROM information_schema.columns "
                        "WHERE table_schema = 'public' AND table_name = 'campushub_user' "
                        "AND column_name = 'student_id') THEN "
                        "ALTER TABLE campushub_user RENAME COLUMN username TO student_id; "
                        "END IF; END $$;"
                    ),
                    reverse_sql=(
                        "DO $$ BEGIN "
                        "IF to_regclass('public.campushub_user') IS NOT NULL "
                        "AND EXISTS (SELECT 1 FROM information_schema.columns "
                        "WHERE table_schema = 'public' AND table_name = 'campushub_user' "
                        "AND column_name = 'student_id') "
                        "AND NOT EXISTS (SELECT 1 FROM information_schema.columns "
                        "WHERE table_schema = 'public' AND table_name = 'campushub_user' "
                        "AND column_name = 'username') THEN "
                        "ALTER TABLE campushub_user RENAME COLUMN student_id TO username; "
                        "END IF; END $$;"
                    ),
                ),
            ],
            state_operations=[
                migrations.RenameField(
                    model_name="campushubuser",
                    old_name="username",
                    new_name="student_id",
                ),
            ],
        ),
    ]
