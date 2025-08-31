from django.test import TestCase
from django.utils import timezone

from trades.models import Trade


class TradeModelTests(TestCase):
    def test_str_contains_type_and_direction(self):
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
        )
        s = str(trade)
        self.assertIn("Crypto", s)
        self.assertIn("Long", s)
