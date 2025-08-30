from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Trade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("crypto", "Crypto"), ("forex", "Forex"), ("index", "Index")], max_length=10)),
                ("price", models.DecimalField(decimal_places=8, max_digits=20)),
                ("stop_loss_price", models.DecimalField(decimal_places=8, max_digits=20)),
                ("volume", models.DecimalField(decimal_places=8, max_digits=20)),
                ("result", models.CharField(choices=[("take", "Take"), ("loss", "Loss")], max_length=10)),
                ("direction", models.CharField(choices=[("long", "Long"), ("short", "Short")], max_length=10)),
                ("date", models.DateTimeField(default=django.utils.timezone.now)),
                ("large_timeframe_image", models.ImageField(blank=True, null=True, upload_to="trades/ltf/")),
                ("medium_timeframe_image", models.ImageField(blank=True, null=True, upload_to="trades/mtf/")),
                ("short_timeframe_image", models.ImageField(blank=True, null=True, upload_to="trades/stf/")),
                ("risk_percent", models.DecimalField(decimal_places=2, help_text="% of account at risk", max_digits=6)),
                ("risk_reward_ratio", models.DecimalField(decimal_places=2, max_digits=8)),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-date", "-created_at"]},
        ),
        migrations.AddField(
            model_name="trade",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="trades", to="trades.tag"),
        ),
    ]

