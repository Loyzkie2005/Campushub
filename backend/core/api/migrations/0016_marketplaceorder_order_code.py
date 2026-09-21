# Generated manually for CampusHub order codes

from django.db import migrations, models


def backfill_order_codes(apps, schema_editor):
    MarketplaceOrder = apps.get_model("api", "MarketplaceOrder")
    import secrets
    import string

    def generate_order_code():
        digits = "".join(secrets.choice(string.digits) for _ in range(4))
        letters = "".join(secrets.choice(string.ascii_uppercase) for _ in range(11))
        return f"{digits}{letters}"

    used = set(
        MarketplaceOrder.objects.exclude(order_code__isnull=True)
        .exclude(order_code="")
        .values_list("order_code", flat=True)
    )
    for order in MarketplaceOrder.objects.filter(
        models.Q(order_code__isnull=True) | models.Q(order_code="")
    ).iterator():
        for _ in range(40):
            code = generate_order_code()
            if code not in used:
                used.add(code)
                order.order_code = code
                order.save(update_fields=["order_code"])
                break


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0015_product_is_archived"),
    ]

    operations = [
        migrations.AddField(
            model_name="marketplaceorder",
            name="order_code",
            field=models.CharField(blank=True, max_length=15, null=True, unique=True),
        ),
        migrations.RunPython(backfill_order_codes, migrations.RunPython.noop),
    ]
