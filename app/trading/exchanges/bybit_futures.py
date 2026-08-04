import asyncio

from pybit.unified_trading import HTTP

from .base import ExchangeBase


class BybitFuturesAdapter(ExchangeBase):
    """
    Bybit USDT Perpetual Futures Adapter.

    Implements the ExchangeBase interface using
    Bybit Unified Trading API.
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

            balance = float(
                coin["walletBalance"]
            )

            if balance <= 0:

                continue

            balances.append(

                {

                    "asset": coin["coin"],

                    "balance": balance,

                    "available": float(
                        coin["availableToWithdraw"]
                    ),

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

            category="linear",

            symbol=symbol,

        )

        return float(

            ticker["result"]["list"][0]["lastPrice"]

        )

    async def get_trading_pairs(self):

        client = await self.connect()

        pairs = await asyncio.to_thread(

            client.get_instruments_info,

            category="linear",

        )

        return sorted(

            item["symbol"]

            for item in pairs["result"]["list"]

        )

    async def get_symbol_info(
        self,
        symbol: str,
    ):

        client = await self.connect()

        info = await asyncio.to_thread(

            client.get_instruments_info,

            category="linear",

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

            category="linear",

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

            category="linear",

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

            category="linear",

            symbol=symbol,

            side="Sell",

            orderType="Market",

            qty=str(quantity),

        )

    async def get_open_positions(self):

        client = await self.connect()

        positions = await asyncio.to_thread(

            client.get_positions,

            category="linear",

            settleCoin="USDT",

        )

        return [

            position

            for position in positions["result"]["list"]

            if float(position["size"]) > 0

        ]

    async def close_position(

        self,

        symbol: str,

    ):

        positions = await self.get_open_positions()

        client = await self.connect()

        for position in positions:

            if position["symbol"] != symbol:

                continue

            quantity = float(position["size"])

            side = (

                "Sell"

                if position["side"] == "Buy"

                else "Buy"

            )

            return await asyncio.to_thread(

                client.place_order,

                category="linear",

                symbol=symbol,

                side=side,

                orderType="Market",

                qty=str(quantity),

                reduceOnly=True,

            )

        return {

            "success": False,

            "message": "No open position found.",

        }