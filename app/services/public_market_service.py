from __future__ import annotations

import asyncio
import json
import socket
import urllib.request
import threading
import time
from typing import Any


class PublicMarketService:
    """Public exchange market-data service used by PQI trial mode.

    Market metadata is cached briefly so the dashboard can populate the pair
    selector quickly without requesting exchangeInfo on every refresh.
    """

    _markets_cache: dict[tuple[str, str], tuple[float, list[str]]] = {}
    _markets_lock = threading.Lock()
    _markets_ttl = 60.0

    @staticmethod
    def _get_json(url: str, params: dict[str, Any] | None = None) -> Any:
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"

        # Force IPv4. Some Windows networks reset IPv6 TLS sessions to exchange APIs.
        original = socket.getaddrinfo

        def ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
            return original(host, port, socket.AF_INET, type, proto, flags)

        socket.getaddrinfo = ipv4_only
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "PlimsolQuantum/1.0"},
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        finally:
            socket.getaddrinfo = original

    @classmethod
    async def markets(cls, exchange="binance", market_type="spot") -> list[str]:
        exchange = (exchange or "binance").lower()
        market_type = (market_type or "spot").lower()
        key = (exchange, market_type)
        now = time.monotonic()

        with cls._markets_lock:
            cached = cls._markets_cache.get(key)
            if cached and now - cached[0] < cls._markets_ttl:
                return list(cached[1])

        if exchange == "bybit":
            category = "linear" if market_type == "futures" else "spot"
            all_items = []
            cursor = None
            # Bybit paginates instruments. Walk every page so the selector
            # exposes every available USDT pair rather than the first 1,000.
            for _ in range(20):
                params = {"category": category, "limit": 1000}
                if cursor:
                    params["cursor"] = cursor
                data = await asyncio.to_thread(
                    cls._get_json,
                    "https://api.bybit.com/v5/market/instruments-info",
                    params,
                )
                result = data.get("result", {})
                all_items.extend(result.get("list", []))
                cursor = result.get("nextPageCursor")
                if not cursor:
                    break
            markets = sorted(
                item["symbol"]
                for item in all_items
                if item.get("status") in (None, "Trading") and item.get("quoteCoin") == "USDT"
            )
        else:
            base = "https://fapi.binance.com" if market_type == "futures" else "https://api.binance.com"
            endpoint = f"{base}/api/v3/exchangeInfo" if market_type == "spot" else f"{base}/fapi/v1/exchangeInfo"
            data = await asyncio.to_thread(cls._get_json, endpoint)
            markets = sorted(
                item["symbol"]
                for item in data.get("symbols", [])
                if item.get("status") == "TRADING" and item.get("quoteAsset") == "USDT"
            )

        with cls._markets_lock:
            cls._markets_cache[key] = (time.monotonic(), markets)
        return list(markets)

    @classmethod
    async def market_available(cls, exchange, market_type, symbol) -> bool:
        compact = (symbol or "").replace("/", "").upper().strip()
        if not compact:
            return False
        return compact in await cls.markets(exchange, market_type)

    @classmethod
    async def candles(cls, exchange, market_type, symbol, interval="1h", limit=120):
        exchange = (exchange or "binance").lower()
        symbol = symbol.replace("/", "").upper()
        if exchange == "bybit":
            interval_map = {"1m": "1", "5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D"}
            data = await asyncio.to_thread(
                cls._get_json,
                "https://api.bybit.com/v5/market/kline",
                {
                    "category": "linear" if market_type == "futures" else "spot",
                    "symbol": symbol,
                    "interval": interval_map.get(interval, "60"),
                    "limit": min(limit, 1000),
                },
            )
            rows = data.get("result", {}).get("list", [])
            rows.reverse()
            return [[int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])] for x in rows]

        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        endpoint = "https://fapi.binance.com/fapi/v1/klines" if market_type == "futures" else "https://api.binance.com/api/v3/klines"
        return await asyncio.to_thread(cls._get_json, endpoint, {"symbol": symbol, "interval": interval_map.get(interval, "1h"), "limit": min(limit, 1000)})

    @classmethod
    async def ticker(cls, exchange, market_type, symbol):
        exchange = (exchange or "binance").lower()
        symbol = symbol.replace("/", "").upper()
        if exchange == "bybit":
            data = await asyncio.to_thread(
                cls._get_json,
                "https://api.bybit.com/v5/market/tickers",
                {"category": "linear" if market_type == "futures" else "spot", "symbol": symbol},
            )
            item = (data.get("result", {}).get("list") or [{}])[0]
            return {
                "last": float(item.get("lastPrice") or 0),
                "bid": float(item.get("bid1Price") or 0),
                "ask": float(item.get("ask1Price") or 0),
                "high": float(item.get("highPrice24h") or 0),
                "low": float(item.get("lowPrice24h") or 0),
                "volume": float(item.get("turnover24h") or 0),
                "percentage": float(item.get("price24hPcnt") or 0) * 100,
            }

        endpoint = "https://fapi.binance.com/fapi/v1/ticker/24hr" if market_type == "futures" else "https://api.binance.com/api/v3/ticker/24hr"
        data = await asyncio.to_thread(cls._get_json, endpoint, {"symbol": symbol})
        return {
            "last": float(data.get("lastPrice") or 0),
            "bid": float(data.get("bidPrice") or 0),
            "ask": float(data.get("askPrice") or 0),
            "high": float(data.get("highPrice") or 0),
            "low": float(data.get("lowPrice") or 0),
            "volume": float(data.get("quoteVolume") or 0),
            "percentage": float(data.get("priceChangePercent") or 0),
        }
