from app.enums.exchange import Exchange
from app.trading.exchanges.binance import BinanceAdapter


class ExchangeFactory:

    @staticmethod
    def create(
        exchange,
        api_key,
        api_secret,
        testnet=False
    ):

        if exchange == Exchange.BINANCE:
            return BinanceAdapter(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet
            )

        raise ValueError(f"Exchange '{exchange.value}' is not yet supported.")