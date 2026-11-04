from django.db import migrations, models


def preserve_existing_batch_tracking(apps, schema_editor):
    Product = apps.get_model("api", "Product")
    Product.objects.using(schema_editor.connection.alias).filter(
        inventory_skus__batches__isnull=False,
    ).exclude(product_type="bundle").update(inventory_method="fifo")


class Migration(migrations.Migration):
    dependencies = [("api", "0050_inventory_movement_notes")]
    operations = [
        migrations.AddField(
            model_name="product", name="inventory_method",
            field=models.CharField(max_length=10, default="simple", db_default="simple",
                choices=[("simple", "Simple stock"), ("fifo", "FIFO batches")]),
        ),
        migrations.AddField(
            model_name="inventorystockmovement", name="reference",
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
        migrations.AddField(
            model_name="inventorystockmovement", name="received_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.RunPython(preserve_existing_batch_tracking, migrations.RunPython.noop),
    ]
