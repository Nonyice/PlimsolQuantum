from app.intelligence.indicator_service import IndicatorService
from app.models.market_snapshot import MarketSnapshot, TimeframeData
from app.trading.exchanges.factory import ExchangeFactory


class MarketObserver:
    TIMEFRAMES = ("1m", "5m", "15m", "1h", "4h", "1d")

    def __init__(self):
        self.indicators = IndicatorService()

    async def observe(self, trading_account, symbol=None):
        credentials = trading_account.get_credentials()
        exchange = ExchangeFactory.create(
            exchange=trading_account.exchange,
            market_type=trading_account.market_type,
            api_key=credentials["api_key"],
            api_secret=credentials["api_secret"],
            testnet=trading_account.is_testnet,
        )
        await exchange.connect()
        symbol = symbol or getattr(trading_account, "symbol", None) or "BTCUSDT"
        snapshot = MarketSnapshot(symbol=symbol, exchange=trading_account.exchange.value)
        for tf in self.TIMEFRAMES:
            candles = await exchange.get_candles(symbol=symbol, interval=tf, limit=300)
            snapshot.timeframes[tf] = TimeframeData(tf, candles, self.indicators.calculate(candles))
        price = await exchange.get_market_price(symbol)
        snapshot.ticker = {"lastPrice": price}
        snapshot.server_time = None
        return snapshot
