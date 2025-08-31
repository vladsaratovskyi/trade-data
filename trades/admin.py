from django.contrib import admin
from .models import Trade, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "type",
        "symbol",
        "direction",
        "price",
        "stop_loss_price",
        "volume",
        "result",
        "risk_percent",
        "risk_reward_ratio",
    )
    list_filter = ("type", "direction", "result", "tags")
    search_fields = ("symbol", "comment")
    autocomplete_fields = ()
    filter_horizontal = ("tags",)
    ordering = ("-date",)
