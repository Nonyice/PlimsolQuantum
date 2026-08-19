from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx


class PublicMarketService:
    """Public exchange market-data service used by PQI trial mode.

    Previous version monkey-patched ``socket.getaddrinfo`` process-wide and
    guarded every single HTTP call with one global ``threading.RLock``. That
    serialised *all* market-data requests for *every* user/pair/timeframe in
    the process, regardless of ``asyncio.gather``. This version uses a
    pooled ``httpx.AsyncClient`` (real keep-alive concurrency) plus a
    short-TTL cache so a 5s scan tick doesn't re-fetch candles that could
    not have changed since the last tick.
    """

    # One pooled client per running event loop (PQI sessions each run their
    # own loop in their own thread, so a single global client would end up
    # bound to whichever loop created it first).
    _clients: dict[int, httpx.AsyncClient] = {}
    _clients_lock = asyncio.Lock()

    _cache: dict[tuple, tuple[float, Any]] = {}
    _cache_locks: dict[tuple, asyncio.Lock] = {}

    # Cache lifetime per candle interval - short enough that data is never
    # stale by more than a fraction of one candle, long enough that a 5s
    # scan loop stops hammering the exchange for timeframes that can't have
    # moved.
    CANDLE_TTL = {
        "1m": 3,
        "5m": 10,
        "15m": 20,
        "1h": 45,
        "4h": 120,
        "1d": 300,
    }
    TICKER_TTL = 2
    MARKETS_TTL = 300

    HEADERS = {"User-Agent": "PlimsolQuantum/1.0"}

    # NOTE: the old code forced IPv4 DNS resolution globally to work around
    # a Windows-specific slow-IPv6-fallback issue. If that resurfaces here,
    # fix it locally via a custom httpx.AsyncHTTPTransport instead of a
    # global socket.getaddrinfo monkeypatch - the global patch is what was
    # serialising every request in the app.

    @classmethod
    async def _client(cls) -> httpx.AsyncClient:
        loop = asyncio.get_running_loop()
        key = id(loop)
        client = cls._clients.get(key)
        if client is not None and not client.is_closed:
            return client
        async with cls._clients_lock:
            client = cls._clients.get(key)
            if client is not None and not client.is_closed:
                return client
            client = httpx.AsyncClient(
                headers=cls.HEADERS,
                timeout=httpx.Timeout(15.0, connect=10.0),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=40,
                ),
            )
            cls._clients[key] = client
            return client

    @classmethod
    async def _get_json(cls, url: str, params: dict[str, Any] | None = None) -> Any:
        client = await cls._client()
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    @classmethod
    async def _cached(cls, cache_key: tuple, ttl: float, fetch):
        now = time.monotonic()
        hit = cls._cache.get(cache_key)
        if hit is not None and now - hit[0] < ttl:
            return hit[1]

        # Per-key lock so N concurrent callers for the same (symbol, tf)
        # collapse into one upstream request instead of N.
        lock = cls._cache_locks.setdefault(cache_key, asyncio.Lock())
        async with lock:
            hit = cls._cache.get(cache_key)
            if hit is not None and time.monotonic() - hit[0] < ttl:
                return hit[1]
            data = await fetch()
            cls._cache[cache_key] = (time.monotonic(), data)
            return data

    @classmethod
    async def markets(cls, exchange="binance", market_type="spot") -> list[str]:
        exchange = (exchange or "binance").lower()
        market_type = (market_type or "spot").lower()

        async def fetch():
            if exchange == "bybit":
                data = await cls._get_json(
                    "https://api.bybit.com/v5/market/instruments-info",
                    {
                        "category": "linear" if market_type == "futures" else "spot",
                        "limit": 1000,
                    },
                )
                return sorted(
                    item["symbol"]
                    for item in data.get("result", {}).get("list", [])
                    if item.get("status") in (None, "Trading") and item.get("quoteCoin") == "USDT"
                )

            base = "https://fapi.binance.com" if market_type == "futures" else "https://api.binance.com"
            data = await cls._get_json(
                f"{base}/api/v3/exchangeInfo" if market_type == "spot" else f"{base}/fapi/v1/exchangeInfo",
            )
            return sorted(
                item["symbol"]
                for item in data.get("symbols", [])
                if item.get("status") == "TRADING" and item.get("quoteAsset") == "USDT"
            )

        return await cls._cached(("markets", exchange, market_type), cls.MARKETS_TTL, fetch)

    @classmethod
    async def candles(cls, exchange, market_type, symbol, interval="1h", limit=120):
        exchange = (exchange or "binance").lower()
        market_type = (market_type or "spot").lower()
        symbol = symbol.replace("/", "").upper()
        ttl = cls.CANDLE_TTL.get(interval, 30)

        async def fetch():
            if exchange == "bybit":
                interval_map = {"1m": "1", "5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D"}
                data = await cls._get_json(
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
                return [
                    [int(x[0]), float(x[1]), float(x[2]), float(x[3]), float(x[4]), float(x[5])]
                    for x in rows
                ]

            interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
            endpoint = (
                "https://fapi.binance.com/fapi/v1/klines"
                if market_type == "futures"
                else "https://api.binance.com/api/v3/klines"
            )
            return await cls._get_json(
                endpoint,
                {
                    "symbol": symbol,
                    "interval": interval_map.get(interval, "1h"),
                    "limit": min(limit, 1000),
                },
            )

        return await cls._cached(
            ("candles", exchange, market_type, symbol, interval, limit),
            ttl,
            fetch,
        )

    @classmethod
    async def ticker(cls, exchange, market_type, symbol):
        exchange = (exchange or "binance").lower()
        market_type = (market_type or "spot").lower()
        symbol = symbol.replace("/", "").upper()

        async def fetch():
            if exchange == "bybit":
                data = await cls._get_json(
                    "https://api.bybit.com/v5/market/tickers",
                    {
                        "category": "linear" if market_type == "futures" else "spot",
                        "symbol": symbol,
                    },
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

            endpoint = (
                "https://fapi.binance.com/fapi/v1/ticker/24hr"
                if market_type == "futures"
                else "https://api.binance.com/api/v3/ticker/24hr"
            )
            data = await cls._get_json(endpoint, {"symbol": symbol})
            return {
                "last": float(data.get("lastPrice") or 0),
                "bid": float(data.get("bidPrice") or 0),
                "ask": float(data.get("askPrice") or 0),
                "high": float(data.get("highPrice") or 0),
                "low": float(data.get("lowPrice") or 0),
                "volume": float(data.get("quoteVolume") or 0),
                "percentage": float(data.get("priceChangePercent") or 0),
            }

        return await cls._cached(("ticker", exchange, market_type, symbol), cls.TICKER_TTL, fetch)

    @classmethod
    async def aclose(cls):
        """Close every pooled client. Call on app/worker shutdown."""
        for client in list(cls._clients.values()):
            if not client.is_closed:
                await client.aclose()
        cls._clients.clear()
