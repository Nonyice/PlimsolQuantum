import time

from app.intelligence.pqi import PQI
from app.intelligence.risk_guardian import RiskGuardian

from app.trading.exchanges.factory import ExchangeFactory
from app.trading.position_monitor import PositionMonitor
from app.trading.trade_executor import TradeExecutor


class TradingService:
    """
    Coordinates the complete trading workflow.

    PQI analyses.

    RiskGuardian protects capital.

    TradeExecutor executes.

    One TradingService instance lives for the lifetime of a BotRunner (one
    per trading_account) and ``run()`` is called on a ~5s tick, so the
    authenticated exchange client and the balance are cached on the
    instance instead of being rebuilt from scratch on every tick.
    """

    # How long a fetched balance stays valid before refetching. A live
    # execution always forces a fresh balance regardless of this TTL.
    BALANCE_TTL = 10

    def __init__(self):

        self.pqi = PQI()

        self.risk_guardian = RiskGuardian()

        self.executor = TradeExecutor()

        self.monitor = PositionMonitor()

        self._exchange = None
        self._exchange_key = None
        self._balance_cache = None
        self._balance_cached_at = 0.0

    def _get_exchange(self, trading_account):
        """Reuse the authenticated exchange client across ticks.

        Rebuilt only if the credentials/market/testnet flag actually
        change, so we're not re-authenticating an exchange client on
        every single scan.
        """
        credentials = trading_account.get_credentials()
        key = (
            trading_account.exchange,
            trading_account.market_type,
            credentials["api_key"],
            trading_account.is_testnet,
        )

        if self._exchange is not None and self._exchange_key == key:
            return self._exchange

        self._exchange = ExchangeFactory.create(
            exchange=trading_account.exchange,
            market_type=trading_account.market_type,
            api_key=credentials["api_key"],
            api_secret=credentials["api_secret"],
            testnet=trading_account.is_testnet,
        )
        self._exchange_key = key
        # Credentials changed underneath us - the cached balance is stale.
        self._balance_cache = None
        self._balance_cached_at = 0.0
        return self._exchange

    async def _get_account_balance(self, exchange, trading_account, force=False):
        now = time.monotonic()
        if (
            not force
            and self._balance_cache is not None
            and (now - self._balance_cached_at) < self.BALANCE_TTL
        ):
            return self._balance_cache

        balances = await exchange.get_account_balance()
        balance = self._get_balance(balances, trading_account.market_type)
        self._balance_cache = balance
        self._balance_cached_at = now
        return balance

    async def run(
        self,
        trading_account,
        capital=None,
        symbol=None,
    ):

        exchange = self._get_exchange(trading_account)

        # Exits take priority over any new trade this tick - a position
        # that has already hit its stop or target should never sit open
        # for another full cycle just because a new opportunity is also
        # being evaluated.
        closed = await self.monitor.check_exits(exchange, trading_account)
        if closed:
            # A close changes the real balance - don't trade this tick on
            # a stale figure.
            self._balance_cache = None

        account_balance = await self._get_account_balance(exchange, trading_account)

        if capital is not None:
            capital = float(capital)
            if capital < 10:
                return {"success": False, "analysis": {}, "message": "Minimum trading capital is $10."}
            if capital > account_balance:
                return {
                    "success": False,
                    "analysis": {},
                    "message": f"Insufficient capital. Available USDT: ${account_balance:,.2f}.",
                }
            account_balance = capital

        snapshot = await self.pqi.observe(
            trading_account,
            symbol=symbol,
        )

        analysis = await self.pqi.analyse(

            snapshot=snapshot,

            trading_account=trading_account,

            account_balance=account_balance,

        )

        risk = self.risk_guardian.evaluate(

            trading_account=trading_account,

            decision=analysis["decision"],

            snapshot=snapshot,

            account_balance=account_balance,

        )

        analysis["risk"] = risk

        if not risk["approved"]:

            return {

                "success": False,

                "analysis": analysis,

                "message": risk["reason"],

            }

        execution = await self.executor.execute(

            exchange=exchange,

            trading_account=trading_account,

            analysis=analysis,

        )

        # A fill changes the real balance - drop the cache so the next
        # tick fetches fresh instead of trading on a stale number.
        self._balance_cache = None

        return {

            "success": True,

            "account_balance": account_balance,

            "analysis": analysis,

            "execution": execution,

            "closed_positions": closed,

        }

    def _get_balance(
        self,
        balances,
        market_type,
    ):

        asset_name = "USDT"

        if market_type.value.upper() == "SPOT":

            for asset in balances:

                if asset["asset"] == asset_name:

                    return float(asset["free"])

        else:

            for asset in balances:

                if asset["asset"] == asset_name:

                    if "available" in asset:

                        return float(asset["available"])

                    return float(asset["balance"])

        return 0.0