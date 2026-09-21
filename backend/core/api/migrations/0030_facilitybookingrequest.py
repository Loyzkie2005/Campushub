from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("api", "0029_facility_is_archived")]

    operations = [
        migrations.CreateModel(
            name="FacilityBookingRequest",
            fields=[
                ("booking", models.OneToOneField(
                    db_constraint=False, on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True, related_name="mobile_request", serialize=False,
                    to="api.booking",
                )),
                ("request_key", models.UUIDField(unique=True)),
                ("details", models.JSONField(default=dict)),
            ],
            options={"db_table": "campushub_facility_booking_request"},
        ),
    ]
