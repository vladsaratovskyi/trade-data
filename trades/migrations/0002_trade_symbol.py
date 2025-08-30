from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trades", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="trade",
            name="symbol",
            field=models.CharField(db_index=True, default="", max_length=50),
        ),
    ]

