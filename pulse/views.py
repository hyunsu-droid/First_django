import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.http import JsonResponse
from django.shortcuts import render

COINS = [
    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "fallback_price": 67248.12, "fallback_change": 2.84},
    {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "fallback_price": 3512.48, "fallback_change": 1.72},
    {"id": "solana", "symbol": "SOL", "name": "Solana", "fallback_price": 182.76, "fallback_change": 4.91},
]

INDEXES = [
    {"symbol": "S&P 500", "query": "%5EGSPC", "fallback_value": 5626.91, "fallback_change": 0.42},
    {"symbol": "NASDAQ", "query": "%5EIXIC", "fallback_value": 17876.77, "fallback_change": 0.68},
    {"symbol": "DXY", "query": "DX-Y.NYB", "fallback_value": 102.41, "fallback_change": -0.18},
]

BRIEFINGS = [
    {"category": "MACRO", "title": "금리 경로와 유동성 변화가 위험자산 변동성을 키우는 구간입니다.", "summary": "달러와 국채 금리의 방향을 함께 확인하며 시장의 리스크 선호를 읽습니다.", "source": "Global Coin Pulse 편집 브리핑"},
    {"category": "GEOPOLITICS", "title": "주요국 정책 발언과 지정학적 긴장을 시장 영향 중심으로 정리합니다.", "summary": "헤드라인보다 가격에 반영될 가능성이 높은 정책 신호에 집중합니다.", "source": "Global Coin Pulse 편집 브리핑"},
    {"category": "ON-CHAIN", "title": "거래소 유입·유출과 BTC 도미넌스로 자금의 방향을 확인합니다.", "summary": "단기 심리와 중기 자금 흐름을 분리해 판단할 수 있도록 구성했습니다.", "source": "Global Coin Pulse 편집 브리핑"},
]

FALLBACK = {
    "coins": [{**coin, "price": coin["fallback_price"], "change_24h": coin["fallback_change"], "status": "fallback"} for coin in COINS],
    "market_cap": 2_480_000_000_000,
    "market_cap_change": 2.31,
    "btc_dominance": 52.8,
    "fear_greed": {"value": 74, "label": "탐욕"},
    "indices": [{"symbol": item["symbol"], "value": item["fallback_value"], "change_24h": item["fallback_change"], "status": "fallback"} for item in INDEXES],
    "status": "fallback",
}


def _get_json(url, params=None, timeout=5):
    query = f"?{urlencode(params)}" if params else ""
    request = Request(f"{url}{query}", headers={"User-Agent": "FirstDjangoMarketBoard/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _index_snapshot():
    values = []
    for item in INDEXES:
        try:
            data = _get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{item['query']}", {"range": "2d", "interval": "1d"}, timeout=4)
            meta = data["chart"]["result"][0]["meta"]
            values.append({"symbol": item["symbol"], "value": meta["regularMarketPrice"], "change_24h": meta.get("regularMarketChangePercent", 0), "status": "live"})
        except (HTTPError, URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
            values.append({"symbol": item["symbol"], "value": item["fallback_value"], "change_24h": item["fallback_change"], "status": "fallback"})
    return values


def _market_snapshot():
    try:
        market_data = _get_json(
            "https://api.coingecko.com/api/v3/coins/markets",
            {"vs_currency": "usd", "ids": ",".join(coin["id"] for coin in COINS), "order": "market_cap_desc", "sparkline": "false", "price_change_percentage": "24h"},
        )
        global_data = _get_json("https://api.coingecko.com/api/v3/global")
        sentiment = _get_json("https://api.alternative.me/fng/", {"limit": 1})
        indices = _index_snapshot()
        coins = []
        for coin in market_data:
            coins.append({
                "id": coin["id"],
                "symbol": coin["symbol"].upper(),
                "name": coin["name"],
                "price": coin.get("current_price", 0),
                "change_24h": coin.get("price_change_percentage_24h") or 0,
                "status": "live",
            })
        fear_value = int(sentiment.get("data", [{}])[0].get("value", 50))
        fear_label = "극단적 탐욕" if fear_value >= 75 else "탐욕" if fear_value >= 55 else "극단적 공포" if fear_value <= 25 else "공포" if fear_value <= 45 else "중립"
        return {
            "coins": coins,
            "market_cap": global_data["data"]["total_market_cap"]["usd"],
            "market_cap_change": global_data["data"]["market_cap_change_percentage_24h_usd"],
            "btc_dominance": global_data["data"]["market_cap_percentage"]["btc"],
            "fear_greed": {"value": fear_value, "label": fear_label},
            "indices": indices,
            "status": "live" if all(item["status"] == "live" for item in indices) else "partial",
            "indices_status": "live" if all(item["status"] == "live" for item in indices) else "partial",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    except (HTTPError, URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError):
        return {**FALLBACK, "updated_at": datetime.now(timezone.utc).isoformat()}


def dashboard(request):
    return render(request, "pulse/dashboard.html", {"briefings": BRIEFINGS, "page_title": "시장 정보 게시판"})


def market_api(request):
    response = _market_snapshot()
    return JsonResponse(response)
