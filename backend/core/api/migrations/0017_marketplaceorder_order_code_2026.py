# Generated manually — switch order codes to 12 chars starting with 2026

from django.db import migrations, models


def regenerate_order_codes(apps, schema_editor):
    MarketplaceOrder = apps.get_model("api", "MarketplaceOrder")
    import secrets
    import string

    def generate_order_code():
        suffix = "".join(secrets.choice(string.ascii_uppercase) for _ in range(8))
        return f"2026{suffix}"

    used = set()
    for order in MarketplaceOrder.objects.all().iterator():
        for _ in range(40):
            code = generate_order_code()
            if code not in used:
                used.add(code)
                order.order_code = code
                order.save(update_fields=["order_code"])
                break


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0016_marketplaceorder_order_code"),
    ]

    operations = [
        # Regenerate first while column is still wide enough for old 15-char values
        migrations.RunPython(regenerate_order_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="marketplaceorder",
            name="order_code",
            field=models.CharField(blank=True, max_length=12, null=True, unique=True),
        ),
    ]
