# Generated manually for CampusHub integrative programming features

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_campushubuser_facility"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasswordResetCode",
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
                ("email", models.EmailField(db_index=True, max_length=254)),
                ("code_hash", models.CharField(max_length=128)),
                ("expires_at", models.DateTimeField()),
                ("used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="ProductInteraction",
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
                ("user_id", models.IntegerField(db_index=True)),
                (
                    "interaction_type",
                    models.CharField(
                        choices=[
                            ("view", "View"),
                            ("click", "Click"),
                            ("purchase", "Purchase"),
                        ],
                        default="view",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interactions",
                        to="api.product",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="productinteraction",
            index=models.Index(
                fields=["user_id", "interaction_type"],
                name="api_product_user_id_0a8f2d_idx",
            ),
        ),
    ]
