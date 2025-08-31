from django import forms
from .models import Trade, Tag, Strategy


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"


class TradeForm(forms.ModelForm):
    # File inputs bound to DB binary fields via save()
    large_timeframe_image = forms.ImageField(required=False, label="Large timeframe image")
    medium_timeframe_image = forms.ImageField(required=False, label="Medium timeframe image")
    short_timeframe_image = forms.ImageField(required=False, label="Short timeframe image")
    new_tags = forms.CharField(
        required=False,
        label="New tags",
        help_text="Comma-separated. New tags will be created.",
        widget=forms.TextInput(attrs={"placeholder": "e.g., breakout, news"}),
    )
    class Meta:
        model = Trade
        fields = [
            "type",
            "symbol",
            "price",
            "stop_loss_price",
            "volume",
            "result",
            "direction",
            "date",
            "risk_percent",
            "risk_reward_ratio",
            "tags",
            "comment",
        ]
        widgets = {
            "date": DateTimeLocalInput(format="%Y-%m-%dT%H:%M"),
            "tags": forms.SelectMultiple(attrs={"class": "form-select", "size": 8}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure datetime-local value renders correctly
        if self.instance and self.instance.pk and self.initial.get("date"):
            self.initial["date"] = self.instance.date.strftime("%Y-%m-%dT%H:%M")
        self.fields["risk_percent"].help_text = "% of account at risk"
        # Order tags alphabetically
        self.fields["tags"].queryset = Tag.objects.order_by("name")
        self.fields["symbol"].help_text = "e.g., ETH/USDT or EUR/USD"
        self.fields["tags"].help_text = "Hold Ctrl/Cmd to select multiple tags"
        # Place fields in a logical order and keep new_tags next to tags
        desired_order = [
            "type",
            "symbol",
            "direction",
            "result",
            "price",
            "stop_loss_price",
            "volume",
            "date",
            "risk_percent",
            "risk_reward_ratio",
            "tags",
            "new_tags",
            "large_timeframe_image",
            "medium_timeframe_image",
            "short_timeframe_image",
            "comment",
        ]
        self.order_fields(desired_order)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        # When commit=True (default in generic views), create and attach new tags
        new_tags_raw = self.cleaned_data.get("new_tags", "")
        if commit and new_tags_raw:
            names = [n.strip() for n in new_tags_raw.split(",") if n.strip()]
            if names:
                for name in names:
                    tag, _ = Tag.objects.get_or_create(name=name)
                    instance.tags.add(tag)

        # Store uploaded images into DB binary fields
        def set_image(kind: str, file_field_name: str):
            f = self.cleaned_data.get(file_field_name)
            if f:
                data = f.read()
                if kind == "large":
                    instance.large_image = data
                    instance.large_image_content_type = getattr(f, "content_type", None) or "application/octet-stream"
                    instance.large_image_name = getattr(f, "name", None) or "large"
                elif kind == "medium":
                    instance.medium_image = data
                    instance.medium_image_content_type = getattr(f, "content_type", None) or "application/octet-stream"
                    instance.medium_image_name = getattr(f, "name", None) or "medium"
                elif kind == "short":
                    instance.short_image = data
                    instance.short_image_content_type = getattr(f, "content_type", None) or "application/octet-stream"
                    instance.short_image_name = getattr(f, "name", None) or "short"

        set_image("large", "large_timeframe_image")
        set_image("medium", "medium_timeframe_image")
        set_image("short", "short_timeframe_image")

        if commit:
            instance.save()
        return instance


class StrategyForm(forms.ModelForm):
    class Meta:
        model = Strategy
        fields = [
            "type",
            "name",
            "pre_session_todo",
            "trading_times",
            "tradable_news",
            "avoid_news",
            "setups",
            "watchlist_pairs",
            "position_management",
            "targets",
            "stop_rules",
        ]
        widgets = {
            "pre_session_todo": forms.Textarea(attrs={"rows": 4, "placeholder": "e.g., review news calendar, update watchlist..."}),
            "trading_times": forms.Textarea(attrs={"rows": 2, "placeholder": "e.g., London session 08:00–11:00, NY 13:00–16:00"}),
            "tradable_news": forms.Textarea(attrs={"rows": 3}),
            "avoid_news": forms.Textarea(attrs={"rows": 3}),
            "setups": forms.Textarea(attrs={"rows": 4}),
            "watchlist_pairs": forms.Textarea(attrs={"rows": 3, "placeholder": "e.g., EUR/USD, GBP/USD, ETH/USDT"}),
            "position_management": forms.Textarea(attrs={"rows": 4}),
            "targets": forms.Textarea(attrs={"rows": 3}),
            "stop_rules": forms.Textarea(attrs={"rows": 3}),
        }
