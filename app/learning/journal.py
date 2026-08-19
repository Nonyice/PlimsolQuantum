from app.extensions import db

from app.models.trade import Trade
from app.models.trade_snapshot import TradeSnapshot
from app.models.trade_outcome import TradeOutcome


class Journal:
    """
    Single entry point for recording
    every trade executed by PQI.
    """

    def record_entry(
        self,
        trade: Trade,
        snapshot: dict,
        analysis: dict,
        decision: dict,
    ):

        db.session.add(trade)

        db.session.flush()

        trade_snapshot = TradeSnapshot(

            trade_id=trade.id,

            market_snapshot=snapshot,

            analysis=analysis,

            decision=decision,

        )

        db.session.add(trade_snapshot)

        db.session.commit()

        return trade

    def record_exit(
        self,
        outcome: TradeOutcome,
    ):

        db.session.add(outcome)

        db.session.commit()

        return outcome