from app.intelligence.pqi import PQI
from app.intelligence.risk_guardian import RiskGuardian

from app.trading.exchanges.factory import ExchangeFactory
from app.trading.trade_executor import TradeExecutor


class TradingService:
    """
    Coordinates the complete trading workflow.

    PQI analyses.

    RiskGuardian protects capital.

    TradeExecutor executes.
    """

    def __init__(self):

        self.pqi = PQI()

        self.risk_guardian = RiskGuardian()

        self.executor = TradeExecutor()

    async def run(
        self,
        trading_account,
    ):

        exchange = ExchangeFactory.create(

            exchange=trading_account.exchange,

            market_type=trading_account.market_type,

            api_key=trading_account.api_key,

            api_secret=trading_account.api_secret,

            testnet=trading_account.is_testnet,

        )

        balances = await exchange.get_account_balance()

        account_balance = self._get_balance(

            balances,

            trading_account.market_type,

        )

        snapshot = await self.pqi.observe(

            trading_account

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

        return {

            "success": True,

            "analysis": analysis,

            "execution": execution,

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