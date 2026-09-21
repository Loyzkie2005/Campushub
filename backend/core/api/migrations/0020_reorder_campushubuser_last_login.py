from django.db import migrations


REORDER_USER_COLUMNS = """
LOCK TABLE campushub_user, campushub_booking, campushub_facility_feedback
    IN ACCESS EXCLUSIVE MODE;

ALTER TABLE campushub_booking
    DROP CONSTRAINT IF EXISTS campushub_booking_user_id_fkey;
ALTER TABLE campushub_facility_feedback
    DROP CONSTRAINT IF EXISTS campushub_facility_feedback_user_id_fkey;

ALTER TABLE campushub_user RENAME TO campushub_user_reorder_old;

CREATE TABLE campushub_user (
    id integer NOT NULL DEFAULT nextval('campushub_user_id_seq'::regclass),
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    student_id character varying(50) NOT NULL,
    email character varying(150) NOT NULL,
    password_hash text NOT NULL,
    last_login timestamp with time zone NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    updated_at timestamp without time zone NOT NULL DEFAULT now()
);

INSERT INTO campushub_user (
    id,
    first_name,
    last_name,
    student_id,
    email,
    password_hash,
    last_login,
    created_at,
    updated_at
)
SELECT
    id,
    first_name,
    last_name,
    student_id,
    email,
    password_hash,
    last_login,
    created_at,
    updated_at
FROM campushub_user_reorder_old;

ALTER SEQUENCE campushub_user_id_seq OWNED BY campushub_user.id;
DROP TABLE campushub_user_reorder_old;

ALTER TABLE campushub_user
    ADD CONSTRAINT campushub_user_pkey PRIMARY KEY (id),
    ADD CONSTRAINT campushub_user_username_key UNIQUE (student_id),
    ADD CONSTRAINT campushub_user_email_key UNIQUE (email);

ALTER TABLE campushub_booking
    ADD CONSTRAINT campushub_booking_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES campushub_user(id) ON DELETE SET NULL;
ALTER TABLE campushub_facility_feedback
    ADD CONSTRAINT campushub_facility_feedback_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES campushub_user(id) ON DELETE SET NULL;

SELECT setval(
    'campushub_user_id_seq',
    COALESCE((SELECT MAX(id) FROM campushub_user), 1),
    EXISTS(SELECT 1 FROM campushub_user)
);
"""


def reorder_legacy_user_columns(apps, schema_editor):
    required_tables = {
        "campushub_user",
        "campushub_booking",
        "campushub_facility_feedback",
    }
    existing_tables = set(schema_editor.connection.introspection.table_names())
    if not required_tables.issubset(existing_tables):
        return

    with schema_editor.connection.cursor() as cursor:
        columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                cursor, "campushub_user"
            )
        }
    if "student_id" not in columns:
        return

    schema_editor.execute(REORDER_USER_COLUMNS)


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0019_campushubuser_last_login"),
    ]

    operations = [
        migrations.RunPython(
            reorder_legacy_user_columns,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
