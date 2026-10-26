from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0043_product_approval_push")]

    operations = [
        migrations.AddField(
            model_name="productapprovalpush", name="decision",
            field=models.CharField(default="approved", max_length=10,
                                   choices=[("approved", "Approved"), ("rejected", "Rejected")]),
        ),
        migrations.RemoveConstraint(model_name="productapprovalpush", name="product_approval_device_once"),
        migrations.AddConstraint(
            model_name="productapprovalpush",
            constraint=models.UniqueConstraint(fields=("product", "device", "approved_at", "decision"),
                                               name="product_review_device_once"),
        ),
    ]
