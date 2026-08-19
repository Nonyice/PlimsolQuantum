import asyncio
import logging

from app.trading.trading_service import TradingService

logger = logging.getLogger("plimsolquantum.bot_runner")


class BotRunner:
    """
    Runs an individual trading account continuously.

    Previously any exception was swallowed with a bare ``print()`` - a
    crashing cycle (e.g. a bad import, an exchange timeout, a bug) would
    fail silently forever, every 5 seconds, with nothing surfaced anywhere.
    Errors are now logged with a traceback, and repeated consecutive
    failures back off instead of retrying a broken cycle every 5s.
    """

    MAX_BACKOFF = 60

    def __init__(
        self,
        trading_account,
        interval=5,
    ):
        self.trading_account = trading_account
        self.interval = interval
        self.service = TradingService()
        self.running = False
        self._consecutive_errors = 0

    async def start(self):

        self.running = True

        while self.running:

            try:

                result = await self.service.run(
                    self.trading_account
                )

                logger.info(
                    "[%s] cycle result: %s",
                    self.trading_account.account_name,
                    result,
                )

                self._consecutive_errors = 0
                wait = self.interval

            except Exception:

                self._consecutive_errors += 1

                logger.exception(
                    "[BOT ERROR] %s (consecutive failures: %d)",
                    self.trading_account.account_name,
                    self._consecutive_errors,
                )

                # Back off on repeated failures so a persistent problem
                # (bad credentials, exchange outage, a bug) doesn't spin
                # the loop every `interval` seconds indefinitely.
                wait = min(
                    self.interval * (2 ** min(self._consecutive_errors, 4)),
                    self.MAX_BACKOFF,
                )

            await asyncio.sleep(wait)

    def stop(self):

        self.running = False
