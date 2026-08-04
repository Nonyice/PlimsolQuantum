from datetime import datetime

from app.enums.trade_status import TradeStatus
from app.learning.journal import Journal
from app.models.trade import Trade


class TradeExecutor:
    """
    Executes approved trades.

    PQI decides.

    TradeExecutor executes.

    Journal records.
    """

    def __init__(self):

        self.journal = Journal()

    async def execute(
        self,
        exchange,
        trading_account,
        analysis,
    ):

        decision = analysis["decision"]

        if not decision["approved"]:

            return {
                "success": False,
                "message": decision["reason"],
            }

        action = decision["action"]

        symbol = decision["symbol"]

        quantity = decision["quantity"]

        if action == "BUY":

            exchange_result = await exchange.place_market_buy(
                symbol=symbol,
                quantity=quantity,
            )

        elif action == "SELL":

            exchange_result = await exchange.place_market_sell(
                symbol=symbol,
                quantity=quantity,
            )

        else:

            return {
                "success": False,
                "message": "Unsupported action.",
            }

        trade = Trade(

            user_id=trading_account.user_id,

            trading_account_id=trading_account.id,

            exchange=trading_account.exchange,

            market_type=trading_account.market_type,

            symbol=symbol,

            timeframe=decision.get("timeframe", "1h"),

            side=action,

            position=decision.get("position", "LONG"),

            leverage=decision.get("leverage", 1),

            risk_percent=decision.get(
                "risk_percent",
                1.0,
            ),

            entry_price=decision["entry_price"],

            stop_loss=decision["stop_loss"],

            take_profit=decision["take_profit"],

            quantity=quantity,

            status=TradeStatus.OPEN,

            opened_at=datetime.utcnow(),
        )

        self.journal.record_entry(

            trade=trade,

            snapshot=analysis["snapshot"],

            analysis={

                "trend": analysis["trend"],

                "momentum": analysis["momentum"],

                "volume": analysis["volume"],

                "volatility": analysis["volatility"],

                "support": analysis["support"],

                "personality": analysis["personality"],

                "opportunity": analysis["opportunity"],

            },

            decision=decision,
        )

        return {

            "success": True,

            "trade_id": trade.id,

            "trade_reference": str(
                trade.trade_reference
            ),

            "exchange": trading_account.exchange.value,

            "market_type":
                trading_account.market_type.value,

            "exchange_response":
                exchange_result,
        }

    async def close_position(
        self,
        exchange,
        symbol,
    ):

        return await exchange.close_position(symbol)