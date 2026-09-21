from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_gmailconfig"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="image_url",
            field=models.TextField(blank=True),
        ),
    ]
