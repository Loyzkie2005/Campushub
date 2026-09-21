import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0021_rename_campushubuser_student_id_to_username"),
    ]

    operations = [
        migrations.AlterField(
            model_name="marketplaceorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("processing", "Processing"),
                    ("ready_for_pickup", "Ready for Pickup"),
                    ("completed", "Completed"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="payment_status",
            field=models.CharField(
                choices=[("unpaid", "Unpaid"), ("paid", "Paid")],
                default="unpaid",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="official_receipt_no",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="payment_encoded_by",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="pickup_location",
            field=models.CharField(blank=True, max_length=180),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="pickup_scheduled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="picked_up_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="cancellation_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="cancelled_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="inventory_deducted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="inventory_restored",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="marketplaceorder",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="MarketplaceOrderStatusHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("previous_status", models.CharField(blank=True, max_length=20)),
                ("new_status", models.CharField(max_length=20)),
                ("changed_by", models.CharField(blank=True, max_length=150)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="api.marketplaceorder",
                    ),
                ),
            ],
            options={
                "db_table": "campushub_order_status_history",
                "ordering": ("-created_at",),
            },
        ),
    ]
