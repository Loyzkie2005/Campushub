from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0010_add_product_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="expiry_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
