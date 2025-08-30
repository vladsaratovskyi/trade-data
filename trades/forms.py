from django import forms
from .models import Trade, Tag


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"


class TradeForm(forms.ModelForm):
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
            "large_timeframe_image",
            "medium_timeframe_image",
            "short_timeframe_image",
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
        return instance
