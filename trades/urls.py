from django.urls import path
from .views import TradeCreateView, TradeListView, TradeUpdateView, stats_view


app_name = "trades"

urlpatterns = [
    path("", TradeListView.as_view(), name="list"),
    path("add/", TradeCreateView.as_view(), name="add"),
    path("edit/<int:pk>/", TradeUpdateView.as_view(), name="edit"),
    path("stats/", stats_view, name="stats"),
]
