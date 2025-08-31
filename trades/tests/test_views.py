from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from trades.models import Trade


class TradeListViewTests(TestCase):
    def setUp(self):
        self.crypto = Trade.objects.create(
            type=Trade.TradeType.CRYPTO,
            symbol="ETH/USDT",
            price=1000,
            stop_loss_price=900,
            volume=1,
            result=Trade.Result.TAKE,
            direction=Trade.Direction.LONG,
            date=timezone.now(),
            risk_percent=1,
            risk_reward_ratio=2,
        )
        self.forex = Trade.objects.create(
            type=Trade.TradeType.FOREX,
            symbol="EUR/USD",
            price=1.2,
            stop_loss_price=1.1,
            volume=1,
            result=Trade.Result.LOSS,
            direction=Trade.Direction.SHORT,
            date=timezone.now(),
            risk_percent=1,
            risk_reward_ratio=2,
        )

    def test_filter_by_type(self):
        url = reverse("trades:list")
        response = self.client.get(url, {"type": Trade.TradeType.CRYPTO})
        trades = list(response.context["trades"])
        self.assertEqual(trades, [self.crypto])


class TradeImageViewTests(TestCase):
    def test_returns_binary_image(self):
        trade = Trade.objects.create(
            type=Trade.TradeType.CRYPTO,
            symbol="BTC/USDT",
            price=10000,
            stop_loss_price=9000,
            volume=1,
            result=Trade.Result.TAKE,
            direction=Trade.Direction.LONG,
            date=timezone.now(),
            risk_percent=1,
            risk_reward_ratio=2,
            large_image=b"data",
            large_image_content_type="image/png",
            large_image_name="test.png",
        )
        url = reverse("trades:image", args=[trade.pk, "ltf"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"data")
        self.assertEqual(response["Content-Type"], "image/png")
