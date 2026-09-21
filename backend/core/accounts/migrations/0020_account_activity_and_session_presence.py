from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0019_expand_role_module_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="admintabtoken",
            name="last_seen_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="AccountActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("account_source", models.CharField(choices=[("admin", "Admin"), ("mobile", "Mobile"), ("unknown", "Unknown")], max_length=12)),
                ("account_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("account_ref", models.CharField(blank=True, db_index=True, max_length=40)),
                ("username", models.CharField(blank=True, max_length=150)),
                ("full_name", models.CharField(blank=True, max_length=220)),
                ("email", models.CharField(blank=True, max_length=254)),
                ("account_type", models.CharField(blank=True, max_length=24)),
                ("role", models.CharField(blank=True, max_length=100)),
                ("activity_type", models.CharField(db_index=True, max_length=40)),
                ("activity", models.CharField(max_length=180)),
                ("module", models.CharField(default="Authentication", max_length=80)),
                ("result", models.CharField(choices=[("success", "Success"), ("failed", "Failed")], max_length=12)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("session_identifier", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "db_table": "campushub_account_activity",
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="accountactivity",
            index=models.Index(fields=["account_source", "account_id", "-created_at"], name="acct_activity_user_idx"),
        ),
        migrations.AddIndex(
            model_name="accountactivity",
            index=models.Index(fields=["activity_type", "result", "-created_at"], name="acct_activity_auth_idx"),
        ),
    ]
