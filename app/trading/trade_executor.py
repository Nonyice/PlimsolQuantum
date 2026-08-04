from datetime import datetime

from app.enums.trade_status import TradeStatus

from app.learning.journal import Journal

from app.models.trade import Trade


class TradeExecutor:
    """
    Executes trades already approved
    by RiskGuardian.
    """

    def __init__(self):

        self.journal = Journal()

    async def execute(
        self,
        exchange,
        trading_account,
        analysis,
    ):

        risk = analysis["risk"]

        if not risk["approved"]:

            return {

                "success": False,

                "message": risk["reason"],

            }

        action = risk["action"]

        symbol = risk["symbol"]

        quantity = risk["quantity"]

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

            timeframe=risk["timeframe"],

            side=action,

            position=risk["position"],

            leverage=risk["leverage"],

            risk_percent=risk["risk_percent"],

            entry_price=risk["entry_price"],

            stop_loss=risk["stop_loss"],

            take_profit=risk["take_profit"],

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

            decision=analysis["decision"],

        )

        return {

            "success": True,

            "trade_id": trade.id,

            "trade_reference": str(
                trade.trade_reference
            ),

            "exchange": trading_account.exchange.value,

            "market_type": trading_account.market_type.value,

            "exchange_response": exchange_result,

        }

    async def close_position(
        self,
        exchange,
        symbol,
    ):

        return await exchange.close_position(symbol)