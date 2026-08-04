import asyncio

from app.trading.exchanges.binance import BinanceAdapter


POPULAR_PAIRS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "LINKUSDT",
    "AVAXUSDT",
    "TRXUSDT"
]


async def main():

    exchange = BinanceAdapter(
        api_key="",
        api_secret="",
        testnet=False
    )

    print("\n=========================================")
    print("        BINANCE MARKET SELECTOR")
    print("=========================================\n")

    for index, pair in enumerate(POPULAR_PAIRS, start=1):
        print(f"{index}. {pair}")

    while True:

        try:
            choice = int(
                input(f"\nChoose a pair (1-{len(POPULAR_PAIRS)}): ")
            )

            if 1 <= choice <= len(POPULAR_PAIRS):
                break

            print("Invalid choice.")

        except ValueError:
            print("Please enter a number.")

    symbol = POPULAR_PAIRS[choice - 1]

    price = await exchange.get_market_price(symbol)

    print("\n-----------------------------------------")
    print(f"Selected Pair : {symbol}")
    print(f"Current Price : {price} USDT")
    print("-----------------------------------------")


if __name__ == "__main__":
    asyncio.run(main())