import asyncio

from app.trading.trading_service import TradingService


class BotRunner:
    """
    Runs an individual trading account continuously.
    """

    def __init__(
        self,
        trading_account,
        interval=5,
    ):
        self.trading_account = trading_account
        self.interval = interval
        self.service = TradingService()
        self.running = False

    async def start(self):

        self.running = True

        while self.running:

            try:

                result = await self.service.run(
                    self.trading_account
                )

                print(result)

            except Exception as e:

                print(
                    f"[BOT ERROR] "
                    f"{self.trading_account.account_name}: {e}"
                )

            await asyncio.sleep(self.interval)

    def stop(self):

        self.running = False