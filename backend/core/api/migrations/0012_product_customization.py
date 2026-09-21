from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0011_add_product_expiry_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="customization_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="product",
            name="customization_options",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="customization",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="marketplaceorder",
            name="option",
            field=models.TextField(blank=True),
        ),
    ]
