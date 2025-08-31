from __future__ import annotations

from django.db.models import Avg, Count, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.views.decorators.http import require_POST
import re
from typing import List, Dict, Optional, Any
import time

try:  # optional, we also support stdlib-only fallback
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:  # optional HTML parser
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

from .forms import TradeForm, StrategyForm
from .models import Tag, Trade, Strategy


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
        # Stats for the currently filtered queryset (not just current page)
        filtered_qs = self.get_queryset()
        total = filtered_qs.count()
        wins = filtered_qs.filter(result=Trade.Result.TAKE).count()
        losses = filtered_qs.filter(result=Trade.Result.LOSS).count()
        win_rate = (wins / total * 100) if total else 0
        avg_rr = filtered_qs.aggregate(v=Avg("risk_reward_ratio"))["v"] or 0
        avg_risk_pct = filtered_qs.aggregate(v=Avg("risk_percent"))["v"] or 0
        by_type = (
            filtered_qs.values("type")
            .annotate(
                total=Count("id"),
                wins=Count("id", filter=Q(result=Trade.Result.TAKE)),
                losses=Count("id", filter=Q(result=Trade.Result.LOSS)),
                avg_rr=Avg("risk_reward_ratio"),
            )
            .order_by("type")
        )
        by_direction = (
            filtered_qs.values("direction")
            .annotate(
                total=Count("id"),
                wins=Count("id", filter=Q(result=Trade.Result.TAKE)),
                losses=Count("id", filter=Q(result=Trade.Result.LOSS)),
                avg_rr=Avg("risk_reward_ratio"),
            )
            .order_by("direction")
        )
        ctx["stats"] = {
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_rr": avg_rr or 0,
            "avg_risk_pct": avg_risk_pct or 0,
            "by_type": list(by_type),
            "by_direction": list(by_direction),
        }
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


class TradeDetailView(DetailView):
    model = Trade
    template_name = "trades/trade_detail.html"
    context_object_name = "trade"


class StrategyListView(ListView):
    model = Strategy
    template_name = "trades/strategy_list.html"
    context_object_name = "strategies"
    paginate_by = 50


class StrategyDetailView(DetailView):
    model = Strategy
    template_name = "trades/strategy_detail.html"
    context_object_name = "strategy"


class StrategyCreateView(CreateView):
    model = Strategy
    form_class = StrategyForm
    template_name = "trades/strategy_form.html"
    success_url = reverse_lazy("trades:strategy_list")


from django.views.generic.edit import DeleteView


class StrategyDeleteView(DeleteView):
    model = Strategy
    template_name = "trades/strategy_confirm_delete.html"
    success_url = reverse_lazy("trades:strategy_list")


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


@require_POST
def bulk_delete_trades(request):
    ids = request.POST.getlist("ids")
    id_ints = []
    for v in ids:
        try:
            id_ints.append(int(v))
        except (TypeError, ValueError):
            continue
    if id_ints:
        Trade.objects.filter(pk__in=id_ints).delete()
    return redirect("trades:list")


def _fetch_forex_factory_html() -> str:
    url = "https://www.forexfactory.com/news"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    timeout = 10
    if requests:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    # Fallback to stdlib
    import urllib.request
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
        return r.read().decode("utf-8", errors="ignore")


def _parse_forex_factory_news(html: str, limit: int = 30) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    base = "https://www.forexfactory.com"
    if BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        # Prefer semantic <article> blocks if present
        articles = soup.select("article")
        for art in articles:
            a = art.find("a", href=True)
            if not a:
                continue
            href = a.get("href", "")
            if href.startswith("/"):
                href = base + href
            title = a.get_text(strip=True) or art.get_text(strip=True)
            if not title:
                continue
            # Optional summary/time if available
            summary = ""
            p = art.find("p")
            if p:
                summary = p.get_text(strip=True)
            time_text = ""
            t = art.find("time")
            if t:
                time_text = t.get_text(strip=True)
            items.append({"title": title, "url": href, "summary": summary, "time": time_text})
            if len(items) >= limit:
                return items
        if items:
            return items
        # Fallback: any links with /news/ in href
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/news/" not in href:
                continue
            title = a.get_text(strip=True)
            if not title:
                continue
            url = href
            if url.startswith("/"):
                url = base + url
            key = (title + url)[:300]
            if key in seen:
                continue
            seen.add(key)
            items.append({"title": title, "url": url, "summary": "", "time": ""})
            if len(items) >= limit:
                break
        return items

    # Regex fallback if BeautifulSoup is unavailable
    for m in re.finditer(r"<a[^>]+href=\"(?P<href>/news/[^\"]+)\"[^>]*>(?P<title>.*?)</a>", html, re.I | re.S):
        raw_title = m.group("title")
        # strip tags
        title = re.sub(r"<[^>]+>", "", raw_title).strip()
        if not title:
            continue
        url = base + m.group("href")
        items.append({"title": title, "url": url, "summary": "", "time": ""})
        if len(items) >= limit:
            break
    return items


_NEWS_CACHE: Dict[str, Any] = {"ts": 0.0, "items": [], "error": None}
_CAL_CACHE: Dict[str, Any] = {"ts": 0.0, "groups": [], "error": None}


def _get_news_cached(force_refresh: bool = False, ttl: int = 600) -> Dict[str, Any]:
    now = time.time()
    if not force_refresh and (now - _NEWS_CACHE["ts"]) < ttl and _NEWS_CACHE["items"]:
        return {"items": _NEWS_CACHE["items"], "error": _NEWS_CACHE["error"]}
    error: Optional[str] = None
    items: List[Dict[str, str]] = []
    try:
        html = _fetch_forex_factory_html()
        items = _parse_forex_factory_news(html, limit=40)
        if not items:
            error = "Could not parse news items from ForexFactory."
    except Exception as exc:  # pragma: no cover - network dependent
        error = "Failed to fetch news."
    _NEWS_CACHE.update({"ts": now, "items": items, "error": error})
    return {"items": items, "error": error}


def _get_calendar_cached(force_refresh: bool = False, ttl: int = 600) -> Dict[str, Any]:
    now = time.time()
    if not force_refresh and (now - _CAL_CACHE["ts"]) < ttl and _CAL_CACHE["groups"]:
        return {"calendar": _CAL_CACHE["groups"], "error": _CAL_CACHE["error"]}
    calendar_error: Optional[str] = None
    calendar: List[Dict[str, object]] = []
    # Prefer JSON calendar API only; avoid HTML fallback that can 403
    try:
        data = _fetch_ff_calendar_json()
        calendar = _parse_ff_calendar_json(data)
    except Exception:  # pragma: no cover - network dependent
        calendar_error = "Calendar feed unavailable (network blocked or rate limited)."
    if not calendar and not calendar_error:
        calendar_error = "Could not parse calendar data from ForexFactory."
    _CAL_CACHE.update({"ts": now, "groups": calendar, "error": calendar_error})
    return {"calendar": calendar, "error": calendar_error}


def news_view(request):
    refresh = request.GET.get("refresh") == "1"
    news_res = _get_news_cached(force_refresh=refresh)
    cal_res = _get_calendar_cached(force_refresh=refresh)
    return render(
        request,
        "trades/news.html",
        {
            "items": news_res["items"],
            "error": news_res["error"],
            "calendar": cal_res["calendar"],
            "calendar_error": cal_res["error"],
        },
    )


def crypto_chart_view(request):
    symbol = (request.GET.get("symbol") or "BTCUSDT").upper()
    # Binance intervals: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M
    interval = (request.GET.get("interval") or "1h").lower()
    if interval not in {"1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"}:
        interval = "1h"
    mode = (request.GET.get("mode") or "candles").lower()
    if mode not in {"candles", "line"}:
        mode = "candles"
    # Limit default candles to reasonable amount for performance
    limit = 500
    context = {
        "symbol": symbol,
        "interval": interval,
        "mode": mode,
        "limit": limit,
        # A few popular symbols for quick access
        "symbols": [
            "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT","DOTUSDT","TRXUSDT","MATICUSDT",
        ],
        "intervals": ["1m","5m","15m","1h","4h","1d"],
    }
    return render(request, "trades/crypto_chart.html", context)


# In-memory cache for Binance klines to reduce rate limits / flakiness
_KLINES_CACHE: Dict[str, Any] = {"data": {}, "ts": {}}


def _fetch_binance_klines(symbol: str, interval: str, limit: int = 500) -> List[List[Any]]:
    base = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": str(limit)}
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
    }
    timeout = 10
    if requests:
        r = requests.get(base, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()  # type: ignore[no-any-return]
    # urllib fallback
    import urllib.parse, urllib.request, json as pyjson
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        return pyjson.loads(resp.read().decode("utf-8", errors="ignore"))


def crypto_klines_api(request):
    symbol = (request.GET.get("symbol") or "BTCUSDT").upper().strip()
    interval = (request.GET.get("interval") or "1h").strip()
    limit_str = request.GET.get("limit") or "500"
    try:
        limit = max(1, min(1000, int(limit_str)))
    except ValueError:
        limit = 500
    allowed = {"1m","3m","5m","15m","30m","1h","2h","4h","6h","8h","12h","1d","3d","1w","1M"}
    if interval not in allowed:
        interval = "1h"

    # Short TTL cache (30s) per (symbol, interval, limit)
    key = f"{symbol}:{interval}:{limit}"
    now = time.time()
    ttl = 30
    cached = _KLINES_CACHE["data"].get(key)
    cts = _KLINES_CACHE["ts"].get(key, 0)
    if cached is not None and (now - cts) < ttl:
        return JsonResponse({"klines": cached})

    try:
        data = _fetch_binance_klines(symbol, interval, limit)
        _KLINES_CACHE["data"][key] = data
        _KLINES_CACHE["ts"][key] = now
        return JsonResponse({"klines": data})
    except Exception as exc:  # pragma: no cover - network dependent
        return JsonResponse({"error": "Failed to fetch Binance data."}, status=502)


def _fetch_forex_factory_calendar_html() -> str:
    url = "https://www.forexfactory.com/calendar"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    timeout = 10
    if requests:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    import urllib.request
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
        return r.read().decode("utf-8", errors="ignore")


def _parse_forex_factory_calendar(html: str) -> List[Dict[str, object]]:
    groups: List[Dict[str, object]] = []
    if not BeautifulSoup:
        return groups
    soup = BeautifulSoup(html, "html.parser")

    # Attempt 1: New FF calendar structure with day containers
    day_containers = soup.select('[data-day], .calendar__day, .day')
    if day_containers:
        for day in day_containers:
            # Day label
            label = day.get("data-day") or day.get_text(strip=True)[:20]
            title_el = day.find(class_=re.compile(r"(calendar__day|day__title|calendar-day|date)", re.I))
            if title_el:
                label = title_el.get_text(strip=True) or label

            events: List[Dict[str, str]] = []
            # Rows within a day
            rows = day.select('[data-event-id], [data-eventid], .calendar__row, tr') or []
            for r in rows:
                # Skip if row is a header with no event
                if r.name == "tr" and r.find("th"):
                    continue
                # Extract fields with flexible selectors
                def pick_text(sel_list: List[str]) -> str:
                    for sel in sel_list:
                        el = r.select_one(sel)
                        if el and el.get_text(strip=True):
                            return el.get_text(strip=True)
                    return ""

                time_txt = pick_text([".time", ".calendar__time", "td.time", "[data-col='time']"]) or "—"
                currency = pick_text([".currency", ".calendar__currency", "td.currency", "[data-col='currency']"]) or ""
                event = pick_text([".event", ".calendar__event-title", "td.event", "[data-col='event']"]) or ""
                if not event:
                    continue

                impact_txt = pick_text([".impact", ".calendar__impact", "td.impact", "[data-col='impact']"]) or ""
                # Normalize impact severity if possible
                severity = ""
                if impact_txt:
                    m = re.search(r"(low|medium|high|holiday|non-economic)", impact_txt, re.I)
                    if m:
                        severity = m.group(1).capitalize()
                if not severity:
                    # Count impact icons as heuristic
                    icons = r.select(".impact img[alt], .impact i")
                    if icons:
                        count = len(icons)
                        severity = {1: "Low", 2: "Medium", 3: "High"}.get(count, "")

                actual = pick_text([".actual", "td.actual", "[data-col='actual']"]) or ""
                forecast = pick_text([".forecast", "td.forecast", "[data-col='forecast']"]) or ""
                previous = pick_text([".previous", "td.previous", "[data-col='previous']"]) or ""
                link_el = r.select_one("a[href]")
                url = link_el.get("href") if link_el else ""
                if url and url.startswith("/"):
                    url = "https://www.forexfactory.com" + url
                events.append(
                    {
                        "time": time_txt,
                        "currency": currency,
                        "event": event,
                        "impact": severity,
                        "actual": actual,
                        "forecast": forecast,
                        "previous": previous,
                        "url": url,
                    }
                )
            if events:
                groups.append({"label": label, "events": events})
        if groups:
            return groups

    # Attempt 2: Global table approach
    table = soup.find("table")
    if table:
        current_label = ""
        events: List[Dict[str, str]] = []
        for row in table.find_all("tr"):
            # Detect day header rows
            if "date" in (row.get("class") or []) or row.find("th"):
                if events and current_label:
                    groups.append({"label": current_label, "events": events})
                    events = []
                current_label = row.get_text(" ", strip=True)
                continue
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 4:
                time_txt = cols[0] or "—"
                currency = cols[1] if len(cols) > 1 else ""
                event = cols[2] if len(cols) > 2 else ""
                impact = cols[3] if len(cols) > 3 else ""
                actual = cols[4] if len(cols) > 4 else ""
                forecast = cols[5] if len(cols) > 5 else ""
                previous = cols[6] if len(cols) > 6 else ""
                if event:
                    events.append({
                        "time": time_txt, "currency": currency, "event": event,
                        "impact": impact, "actual": actual, "forecast": forecast, "previous": previous, "url": ""
                    })
        if events and current_label:
            groups.append({"label": current_label, "events": events})
    return groups


def _fetch_ff_calendar_json() -> List[Dict[str, Any]]:
    # Known endpoints mirrored on FF CDN; try in order
    endpoints = [
        "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
        "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json,text/plain,*/*",
    }
    timeout = 10
    last_exc: Optional[Exception] = None
    if requests:
        for url in endpoints:
            try:
                resp = requests.get(url, headers=headers, timeout=timeout)
                if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("application/json"):
                    return resp.json()  # type: ignore[no-any-return]
                # Some CDNs return text/plain
                if resp.status_code == 200:
                    return resp.json()
            except Exception as exc:  # pragma: no cover
                last_exc = exc
                continue
        if last_exc:
            raise last_exc
    # urllib fallback
    import urllib.request, json as pyjson
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310
                data = r.read().decode("utf-8", errors="ignore")
                return pyjson.loads(data)
        except Exception as exc:  # pragma: no cover
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
    return []


def _parse_ff_calendar_json(data: List[Dict[str, Any]]) -> List[Dict[str, object]]:
    if not data:
        return []
    # Normalize and group by date (YYYY-MM-DD)
    groups_map: Dict[str, List[Dict[str, str]]] = {}

    def norm_impact(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return {1: "Low", 2: "Medium", 3: "High"}.get(int(v), "")
        s = str(v).strip().lower()
        if "high" in s:
            return "High"
        if "medium" in s or "med" in s:
            return "Medium"
        if "low" in s:
            return "Low"
        return s.capitalize() if s else ""

    for ev in data:
        # Attempt to support a few possible schemas
        title = (ev.get("title") or ev.get("event") or "").strip()
        if not title:
            continue
        country = (ev.get("country") or ev.get("currency") or "").strip()
        impact = norm_impact(ev.get("impact"))
        url = ev.get("id")
        if url:
            url = f"https://www.forexfactory.com/calendar?event={url}"
        else:
            url = ""
        # Time handling: many feeds include either timestamp (seconds) or datetime string
        t_raw = ev.get("timestamp") or ev.get("time") or ev.get("date") or ""
        date_key = ""
        time_txt = "—"
        if isinstance(t_raw, (int, float)):
            import datetime as _dt
            dt = _dt.datetime.utcfromtimestamp(int(t_raw))
            date_key = dt.strftime("%Y-%m-%d")
            time_txt = dt.strftime("%H:%M")
        else:
            s = str(t_raw)
            # Expected like "2025-08-31 13:30:00" or "2025-08-31T13:30:00Z"
            m = re.match(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})", s)
            if m:
                date_key, time_txt = m.group(1), m.group(2)
            elif re.match(r"\d{4}-\d{2}-\d{2}$", s):
                date_key, time_txt = s, "—"
        if not date_key:
            # Put unknown dates under a generic label
            date_key = "Unknown Date"

        actual = (ev.get("actual") or ev.get("actualValue") or "").strip() if isinstance(ev.get("actual"), str) or isinstance(ev.get("actualValue"), str) else (str(ev.get("actual")) if ev.get("actual") is not None else "")
        forecast = (ev.get("forecast") or ev.get("forecastValue") or "").strip() if isinstance(ev.get("forecast"), str) or isinstance(ev.get("forecastValue"), str) else (str(ev.get("forecast")) if ev.get("forecast") is not None else "")
        previous = (ev.get("previous") or ev.get("previousValue") or "").strip() if isinstance(ev.get("previous"), str) or isinstance(ev.get("previousValue"), str) else (str(ev.get("previous")) if ev.get("previous") is not None else "")

        groups_map.setdefault(date_key, []).append({
            "time": time_txt,
            "currency": country,
            "event": title,
            "impact": impact,
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
            "url": url,
        })

    # Sort groups by date where possible
    def sort_key(k: str) -> Any:
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", k)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return (9999, 12, 31, k)

    groups: List[Dict[str, object]] = []
    for k in sorted(groups_map.keys(), key=sort_key):
        events = groups_map[k]
        # sort events by time within day
        def ekey(e: Dict[str, str]) -> Any:
            m = re.match(r"(\d{2}):(\d{2})", e.get("time") or "")
            return (int(m.group(1)), int(m.group(2))) if m else (99, 99)
        events.sort(key=ekey)
        groups.append({"label": k, "events": events})
    return groups
