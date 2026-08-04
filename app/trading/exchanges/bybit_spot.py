import asyncio

from pybit.unified_trading import HTTP

from .base import ExchangeBase


class BybitSpotAdapter(ExchangeBase):
    """
    Bybit Spot Exchange Adapter.

    Implements the ExchangeBase interface using
    Bybit's Unified Trading API.
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

        self.client = HTTP(

            api_key=self.api_key,

            api_secret=self.api_secret,

            testnet=self.testnet,

        )

        return self.client

    async def validate_credentials(self):

        client = await self.connect()

        try:

            await asyncio.to_thread(
                client.get_wallet_balance,
                accountType="UNIFIED",
            )

            return True

        except Exception as exc:

            print(exc)

            return False

    async def get_account_balance(self):

        client = await self.connect()

        wallet = await asyncio.to_thread(

            client.get_wallet_balance,

            accountType="UNIFIED",

        )

        balances = []

        coins = wallet["result"]["list"][0]["coin"]

        for coin in coins:

            wallet_balance = float(
                coin["walletBalance"]
            )

            if wallet_balance <= 0:

                continue

            balances.append(

                {

                    "asset": coin["coin"],

                    "free": float(
                        coin["availableToWithdraw"]
                    ),

                    "locked": (
                        wallet_balance
                        - float(
                            coin["availableToWithdraw"]
                        )
                    ),

                    "total": wallet_balance,

                }

            )

        return balances

    async def get_market_price(
        self,
        symbol: str,
    ):

        client = await self.connect()

        ticker = await asyncio.to_thread(

            client.get_tickers,

            category="spot",

            symbol=symbol,

        )

        return float(

            ticker["result"]["list"][0]["lastPrice"]

        )

    async def get_trading_pairs(self):

        client = await self.connect()

        symbols = await asyncio.to_thread(

            client.get_instruments_info,

            category="spot",

        )

        return sorted(

            item["symbol"]

            for item in symbols["result"]["list"]

        )

    async def get_symbol_info(
        self,
        symbol: str,
    ):

        client = await self.connect()

        info = await asyncio.to_thread(

            client.get_instruments_info,

            category="spot",

            symbol=symbol,

        )

        return info["result"]["list"][0]

    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ):

        client = await self.connect()

        return await asyncio.to_thread(

            client.get_kline,

            category="spot",

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

            client.place_order,

            category="spot",

            symbol=symbol,

            side="Buy",

            orderType="Market",

            qty=str(quantity),

        )

    async def place_market_sell(
        self,
        symbol: str,
        quantity: float,
    ):

        client = await self.connect()

        return await asyncio.to_thread(

            client.place_order,

            category="spot",

            symbol=symbol,

            side="Sell",

            orderType="Market",

            qty=str(quantity),

        )

    async def get_open_positions(self):

        client = await self.connect()

        return await asyncio.to_thread(

            client.get_open_orders,

            category="spot",

        )

    async def close_position(
        self,
        symbol: str,
    ):

        info = await self.get_symbol_info(
            symbol,
        )

        base_asset = info["baseCoin"]

        balances = await self.get_account_balance()

        quantity = 0.0

        for balance in balances:

            if balance["asset"] == base_asset:

                quantity = balance["free"]

                break

        if quantity <= 0:

            return {

                "success": False,

                "message": f"No {base_asset} available.",

            }

        return await self.place_market_sell(

            symbol=symbol,

            quantity=quantity,

        )