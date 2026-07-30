from binance.spot import Spot

from .base import ExchangeBase


class BinanceAdapter(ExchangeBase):
    """
    Binance Exchange Adapter

    This class implements all exchange operations required by PQI.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.client = None

    async def connect(self):
        """
        Connect to Binance using the official SDK.
        """

        if self.client is not None:
            return self.client

        base_url = (
            "https://testnet.binance.vision"
            if self.testnet
            else "https://api.binance.com"
        )

        self.client = Spot(
            api_key=self.api_key,
            api_secret=self.api_secret,
            base_url=base_url
        )

        return self.client

    async def validate_credentials(self):
        """
        Validate the supplied API credentials.
        """

        client = await self.connect()

        try:
            client.account()
            return True

        except Exception as e:

            print(f"Binance Authentication Error: {e}")
        return False

    async def get_account_balance(self):
        """
        Retrieve account balances.
        """

        client = await self.connect()

        account = client.account()

        balances = []

        for asset in account["balances"]:
            free = float(asset["free"])
            locked = float(asset["locked"])

            if free > 0 or locked > 0:
                balances.append({
                    "asset": asset["asset"],
                    "free": free,
                    "locked": locked,
                    "total": free + locked
                })

        return balances

    async def get_market_price(self, symbol: str):
        """
        Get the latest market price.
        """

        client = await self.connect()

        ticker = client.ticker_price(symbol=symbol)

        return float(ticker["price"])

    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ):
        """
        Retrieve historical candlestick data.
        """

        client = await self.connect()

        return client.klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )

    async def place_market_buy(
        self,
        symbol: str,
        quantity: float
    ):
        raise NotImplementedError("Market buy not implemented yet.")

    async def place_market_sell(
        self,
        symbol: str,
        quantity: float
    ):
        raise NotImplementedError("Market sell not implemented yet.")

    async def get_open_positions(self):
        raise NotImplementedError("Open positions not implemented yet.")

    async def close_position(self, symbol: str):
        raise NotImplementedError("Close position not implemented yet.")