import io

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from PIL import Image

from trades.forms import TradeForm
from trades.models import Tag, Trade


class TradeFormTests(TestCase):
    def _create_image(self):
        buffer = io.BytesIO()
        Image.new("RGB", (1, 1)).save(buffer, format="PNG")
        return buffer.getvalue()

    def test_new_tags_and_image_saved(self):
        img_bytes = self._create_image()
        uploaded = SimpleUploadedFile("test.png", img_bytes, content_type="image/png")
        form = TradeForm(
            data={
                "type": Trade.TradeType.CRYPTO,
                "symbol": "ETH/USDT",
                "price": 1000,
                "stop_loss_price": 900,
                "volume": 1,
                "result": Trade.Result.TAKE,
                "direction": Trade.Direction.LONG,
                "date": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "risk_percent": 1,
                "risk_reward_ratio": 2,
                "new_tags": "breakout",
            },
            files={"large_timeframe_image": uploaded},
        )
        self.assertTrue(form.is_valid(), form.errors)
        trade = form.save()
        self.assertTrue(Tag.objects.filter(name="breakout").exists())
        self.assertIsNotNone(trade.large_image)
        self.assertTrue(trade.tags.filter(name="breakout").exists())
