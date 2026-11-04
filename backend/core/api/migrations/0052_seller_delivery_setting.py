from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("api", "0051_hybrid_inventory")]
    operations = [migrations.AlterField(
        model_name="marketplaceorder", name="fulfillment_method",
        field=models.CharField(max_length=20, blank=True, default="",
            choices=[("pickup", "Customer Pickup"), ("seller_delivery", "Seller Delivery")])),
        migrations.AddField(
        model_name="sellerrequest", name="seller_delivery_enabled",
        field=models.BooleanField(default=False, db_default=False))]
