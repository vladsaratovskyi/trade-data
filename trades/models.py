from __future__ import annotations

from django.db import models
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - for admin/readability
        return self.name


class Trade(models.Model):
    class TradeType(models.TextChoices):
        CRYPTO = "crypto", "Crypto"
        FOREX = "forex", "Forex"
        INDEX = "index", "Index"

    class Result(models.TextChoices):
        TAKE = "take", "Take"
        LOSS = "loss", "Loss"

    class Direction(models.TextChoices):
        LONG = "long", "Long"
        SHORT = "short", "Short"

    type = models.CharField(max_length=10, choices=TradeType.choices)
    symbol = models.CharField(max_length=50, default="", db_index=True)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    stop_loss_price = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=20, decimal_places=8)
    result = models.CharField(max_length=10, choices=Result.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    date = models.DateTimeField(default=timezone.now)

    large_timeframe_image = models.ImageField(
        upload_to="trades/ltf/", null=True, blank=True
    )
    medium_timeframe_image = models.ImageField(
        upload_to="trades/mtf/", null=True, blank=True
    )
    short_timeframe_image = models.ImageField(
        upload_to="trades/stf/", null=True, blank=True
    )

    risk_percent = models.DecimalField(max_digits=6, decimal_places=2, help_text="% of account at risk")
    risk_reward_ratio = models.DecimalField(max_digits=8, decimal_places=2)
    tags = models.ManyToManyField(Tag, related_name="trades", blank=True)
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.get_type_display()} {self.get_direction_display()} {self.date:%Y-%m-%d %H:%M}"
