from __future__ import annotations

from django.db.models import Avg, Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import TradeForm
from .models import Tag, Trade


class TradeListView(ListView):
    model = Trade
    template_name = "trades/trade_list.html"
    context_object_name = "trades"
    paginate_by = 25

    def get_queryset(self):
        qs = Trade.objects.select_related().prefetch_related("tags").all()

        types = self.request.GET.getlist("type")
        results = self.request.GET.getlist("result")
        directions = self.request.GET.getlist("direction")
        tags = self.request.GET.getlist("tags")  # tag ids
        symbol = (self.request.GET.get("symbol") or "").strip()

        if types:
            qs = qs.filter(type__in=types)
        if results:
            qs = qs.filter(result__in=results)
        if directions:
            qs = qs.filter(direction__in=directions)
        if tags:
            try:
                tag_ids = [int(t) for t in tags]
                qs = qs.filter(tags__id__in=tag_ids).distinct()
            except ValueError:
                pass
        if symbol:
            qs = qs.filter(symbol__icontains=symbol)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["all_tags"] = Tag.objects.order_by("name")
        ctx["selected_types"] = set(self.request.GET.getlist("type"))
        ctx["selected_results"] = set(self.request.GET.getlist("result"))
        ctx["selected_directions"] = set(self.request.GET.getlist("direction"))
        try:
            ctx["selected_tags"] = {int(t) for t in self.request.GET.getlist("tags")}
        except ValueError:
            ctx["selected_tags"] = set()
        ctx["q_symbol"] = (self.request.GET.get("symbol") or "").strip()
        # For suggestions in filter UI
        ctx["all_symbols"] = (
            Trade.objects.exclude(symbol="").values_list("symbol", flat=True)
            .distinct().order_by("symbol")
        )
        return ctx


class TradeCreateView(CreateView):
    model = Trade
    form_class = TradeForm
    template_name = "trades/trade_form.html"
    success_url = reverse_lazy("trades:list")


class TradeUpdateView(UpdateView):
    model = Trade
    form_class = TradeForm
    template_name = "trades/trade_form.html"
    success_url = reverse_lazy("trades:list")


def stats_view(request):
    qs = Trade.objects.all()

    total = qs.count()
    wins = qs.filter(result=Trade.Result.TAKE).count()
    losses = qs.filter(result=Trade.Result.LOSS).count()
    win_rate = (wins / total * 100) if total else 0

    avg_rr = qs.aggregate(v=Avg("risk_reward_ratio"))["v"] or 0
    avg_risk_pct = qs.aggregate(v=Avg("risk_percent"))["v"] or 0

    by_type = (
        qs.values("type")
        .annotate(
            total=Count("id"),
            wins=Count("id", filter=Q(result=Trade.Result.TAKE)),
            losses=Count("id", filter=Q(result=Trade.Result.LOSS)),
            avg_rr=Avg("risk_reward_ratio"),
        )
        .order_by("type")
    )

    by_direction = (
        qs.values("direction")
        .annotate(
            total=Count("id"),
            wins=Count("id", filter=Q(result=Trade.Result.TAKE)),
            losses=Count("id", filter=Q(result=Trade.Result.LOSS)),
            avg_rr=Avg("risk_reward_ratio"),
        )
        .order_by("direction")
    )

    context = {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_rr": avg_rr or 0,
        "avg_risk_pct": avg_risk_pct or 0,
        "by_type": list(by_type),
        "by_direction": list(by_direction),
    }
    return render(request, "trades/stats.html", context)


def trade_image(request, pk: int, kind: str):
    trade = get_object_or_404(Trade, pk=pk)
    if kind == "ltf":
        data = trade.large_image
        ct = trade.large_image_content_type or "application/octet-stream"
        filename = trade.large_image_name or "large"
    elif kind == "mtf":
        data = trade.medium_image
        ct = trade.medium_image_content_type or "application/octet-stream"
        filename = trade.medium_image_name or "medium"
    elif kind == "stf":
        data = trade.short_image
        ct = trade.short_image_content_type or "application/octet-stream"
        filename = trade.short_image_name or "short"
    else:
        raise Http404("Unknown image kind")

    if not data:
        raise Http404("No image")
    if isinstance(data, memoryview):
        data = data.tobytes()
    resp = HttpResponse(data, content_type=ct)
    resp["Content-Disposition"] = f"inline; filename=\"{filename}\""
    return resp
