from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0049_mobile_food_preferences")]
    operations = [
        migrations.AddField(
            model_name="inventorystockmovement", name="notes",
            field=models.TextField(max_length=500, blank=True, null=True),
        ),
    ]
