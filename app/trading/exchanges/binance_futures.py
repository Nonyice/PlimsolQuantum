import asyncio

from binance.um_futures import UMFutures

from .base import ExchangeBase


class BinanceFuturesAdapter(ExchangeBase):
    """
    Binance USDT-M Futures Adapter.

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

            "https://testnet.binancefuture.com"

            if self.testnet

            else "https://fapi.binance.com"

        )

        self.client = UMFutures(

            key=self.api_key,

            secret=self.api_secret,

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

    async def get_account_balance(self):

        client = await self.connect()

        account = await asyncio.to_thread(
            client.balance,
        )

        balances = []

        for asset in account:

            balance = float(asset["balance"])

            if balance <= 0:

                continue

            balances.append(

                {

                    "asset": asset["asset"],

                    "balance": balance,

                    "available": float(
                        asset["availableBalance"]
                    ),

                }

            )

        return balances

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

        client = await self.connect()

        positions = await asyncio.to_thread(
            client.position_information,
        )

        return [

            position

            for position in positions

            if abs(float(position["positionAmt"])) > 0

        ]

    async def close_position(
        self,
        symbol: str,
    ):

        client = await self.connect()

        positions = await self.get_open_positions()

        for position in positions:

            if position["symbol"] != symbol:

                continue

            quantity = abs(
                float(position["positionAmt"])
            )

            side = (

                "SELL"

                if float(position["positionAmt"]) > 0

                else "BUY"

            )

            return await asyncio.to_thread(

                client.new_order,

                symbol=symbol,

                side=side,

                type="MARKET",

                quantity=quantity,

                reduceOnly="true",

            )

        return {

            "success": False,

            "message": "No open position found.",

        }