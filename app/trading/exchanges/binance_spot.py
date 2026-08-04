import asyncio

from binance.spot import Spot

from .base import ExchangeBase


class BinanceSpotAdapter(ExchangeBase):
    """
    Binance Spot Exchange Adapter.

    All Binance SDK calls are executed in asyncio.to_thread()
    because the official SDK is synchronous.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
    ):

        self.api_key = api_key

        self.api_secret = api_secret

        self.testnet = testnet

        self.client = None

    async def connect(self):

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
            base_url=base_url,
        )

        return self.client

    async def validate_credentials(self):

        client = await self.connect()

        try:

            await asyncio.to_thread(
                client.account,
            )

            return True

        except Exception as exc:

            print(exc)

            return False

    async def get_account_balance(self):

        client = await self.connect()

        account = await asyncio.to_thread(
            client.account,
        )

        balances = []

        for asset in account["balances"]:

            free = float(asset["free"])

            locked = float(asset["locked"])

            if free == 0 and locked == 0:

                continue

            balances.append(

                {
                    "asset": asset["asset"],
                    "free": free,
                    "locked": locked,
                    "total": free + locked,
                }

            )

        return balances

    async def get_market_price(
        self,
        symbol: str,
    ):

        client = await self.connect()

        ticker = await asyncio.to_thread(
            client.ticker_price,
            symbol=symbol,
        )

        return float(ticker["price"])

    async def get_trading_pairs(self):

        client = await self.connect()

        exchange = await asyncio.to_thread(
            client.exchange_info,
        )

        return sorted(

            symbol["symbol"]

            for symbol in exchange["symbols"]

            if symbol["status"] == "TRADING"

        )

    async def get_symbol_info(
        self,
        symbol: str,
    ):

        client = await self.connect()

        info = await asyncio.to_thread(
            client.exchange_info,
            symbol=symbol,
        )

        return info["symbols"][0]

    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ):

        client = await self.connect()

        return await asyncio.to_thread(
            client.klines,
            symbol=symbol,
            interval=interval,
            limit=limit,
        )

    async def place_market_buy(
        self,
        symbol: str,
        quantity: float,
    ):

        client = await self.connect()

        return await asyncio.to_thread(
            client.new_order,
            symbol=symbol,
            side="BUY",
            type="MARKET",
            quantity=quantity,
        )

    async def place_market_sell(
        self,
        symbol: str,
        quantity: float,
    ):

        client = await self.connect()

        return await asyncio.to_thread(
            client.new_order,
            symbol=symbol,
            side="SELL",
            type="MARKET",
            quantity=quantity,
        )

    async def get_open_positions(self):
        """
        Spot has no positions.

        Return open orders to satisfy the interface.
        """

        client = await self.connect()

        return await asyncio.to_thread(
            client.get_open_orders,
        )

    async def close_position(
        self,
        symbol: str,
    ):

        info = await self.get_symbol_info(
            symbol,
        )

        base_asset = info["baseAsset"]

        balances = await self.get_account_balance()

        quantity = 0.0

        for balance in balances:

            if balance["asset"] == base_asset:

                quantity = balance["free"]

                break

        if quantity <= 0:

            return {

                "success": False,

                "message": (
                    f"No {base_asset} available."
                ),

            }

        return await self.place_market_sell(
            symbol=symbol,
            quantity=quantity,
        )