from django.urls import path
from .views import TradeCreateView, TradeListView, TradeUpdateView, stats_view, trade_image


app_name = "trades"

urlpatterns = [
    path("", TradeListView.as_view(), name="list"),
    path("add/", TradeCreateView.as_view(), name="add"),
    path("edit/<int:pk>/", TradeUpdateView.as_view(), name="edit"),
    path("image/<int:pk>/<str:kind>/", trade_image, name="image"),  # kind: ltf|mtf|stf
    path("stats/", stats_view, name="stats"),
]
