import traceback
import asyncio

from app.trading.exchanges.binance import BinanceAdapter


async def main():
    try:
        exchange = BinanceAdapter(
            api_key="",
            api_secret="",
            testnet=False
        )

        price = await exchange.get_market_price("BTCUSDT")
        print(price)

    except Exception:
        traceback.print_exc()


asyncio.run(main())