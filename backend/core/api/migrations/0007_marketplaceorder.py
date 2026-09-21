from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_product_image_url_textfield"),
    ]

    operations = [
        migrations.CreateModel(
            name="MarketplaceOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("buyer_user_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("buyer_name", models.CharField(blank=True, max_length=150)),
                ("buyer_email", models.EmailField(blank=True, max_length=254)),
                ("product_name", models.CharField(max_length=150)),
                ("category", models.CharField(blank=True, max_length=80)),
                ("seller_name", models.CharField(blank=True, max_length=150)),
                ("seller_contact", models.CharField(blank=True, max_length=180)),
                ("option", models.CharField(blank=True, max_length=40)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("unit_price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("total_price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("image_url", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="marketplace_orders",
                        to="api.product",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
