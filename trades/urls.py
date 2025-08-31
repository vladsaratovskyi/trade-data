from django.urls import path
from .views import (
    TradeCreateView,
    TradeListView,
    TradeUpdateView,
    TradeDetailView,
    StrategyListView,
    StrategyDetailView,
    StrategyCreateView,
    StrategyDeleteView,
    stats_view,
    trade_image,
    bulk_delete_trades,
    news_view,
)


app_name = "trades"

urlpatterns = [
    path("", TradeListView.as_view(), name="list"),
    path("add/", TradeCreateView.as_view(), name="add"),
    path("edit/<int:pk>/", TradeUpdateView.as_view(), name="edit"),
    path("view/<int:pk>/", TradeDetailView.as_view(), name="detail"),
    # Strategies
    path("strategies/", StrategyListView.as_view(), name="strategy_list"),
    path("strategies/add/", StrategyCreateView.as_view(), name="strategy_add"),
    path("strategies/view/<int:pk>/", StrategyDetailView.as_view(), name="strategy_detail"),
    path("strategies/delete/<int:pk>/", StrategyDeleteView.as_view(), name="strategy_delete"),
    path("bulk-delete/", bulk_delete_trades, name="bulk_delete"),
    path("image/<int:pk>/<str:kind>/", trade_image, name="image"),  # kind: ltf|mtf|stf
    path("stats/", stats_view, name="stats"),
    path("news/", news_view, name="news"),
]
