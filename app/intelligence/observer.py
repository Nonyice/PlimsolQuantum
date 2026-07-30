from dataclasses import dataclass
from typing import List

from app.trading.exchanges.factory import ExchangeFactory


@dataclass
class MarketSnapshot:
    symbol: str
    price: float
    trend: str
    trend_strength: float
    momentum: float
    volume: float
    volatility: float
    support: float
    resistance: float
    confidence: float
    healthy: bool
    reasons: List[str]


class MarketObserver:

    async def observe(self, trading_account):

        exchange = ExchangeFactory.create(
            exchange=trading_account.exchange,
            api_key=trading_account.api_key,
            api_secret=trading_account.api_secret,
            testnet=trading_account.is_testnet
        )

        symbol = trading_account.symbol

        price = await exchange.get_market_price(symbol)

        candles = await exchange.get_candles(
            symbol=symbol,
            interval="1m",
            limit=200
        )

        return self._analyse_market(
            symbol=symbol,
            price=price,
            candles=candles
        )

    def _analyse_market(self, symbol, price, candles):

        return MarketSnapshot(
            symbol=symbol,
            price=price,
            trend="UNKNOWN",
            trend_strength=0.0,
            momentum=0.0,
            volume=0.0,
            volatility=0.0,
            support=0.0,
            resistance=0.0,
            confidence=0.0,
            healthy=False,
            reasons=[]
        )