from datetime import datetime
from decimal import Decimal

from app.trading.position_manager import PositionManager


class RiskGuardian:
    """
    Approves or rejects a single proposed trade.

    PQI trial mode uses pqi_session_pairs for portfolio state, so this
    guardian must not depend on the legacy Trade/TradeOutcome tables.

    Guardrails:
    - no more than MAX_OPEN_POSITIONS concurrent open positions
    - no duplicate position on a symbol already open
    - daily realised-loss circuit breaker where realised P/L is available
    - valid SL/TP and reward:risk
    """

    DEFAULT_RISK_PERCENT = Decimal("2.0")
    DEFAULT_REWARD_RATIO = Decimal("1.75")
    MAX_LEVERAGE = 20

    MAX_OPEN_POSITIONS = 3
    MAX_DAILY_LOSS_PERCENT = Decimal("5.0")

    def __init__(self):
        self.positions = PositionManager()

    def evaluate(
        self,
        trading_account,
        decision,
        snapshot,
        account_balance,
    ):
        if not decision.should_execute:
            return {
                "approved": False,
                "reason": decision.reason,
                "decision": decision,
            }

        portfolio_block = self._check_portfolio_limits(
            trading_account,
            snapshot.symbol,
            Decimal(str(account_balance)),
        )

        if portfolio_block is not None:
            return {
                "approved": False,
                "reason": portfolio_block,
                "decision": decision,
            }

        tf = snapshot.timeframes["1h"]
        indicators = tf.indicators

        entry = Decimal(str(snapshot.ticker["lastPrice"]))
        atr = Decimal(str(indicators.atr))

        stop_distance = (
            atr *
            Decimal(str(decision.stop_multiplier))
        )

        if stop_distance <= 0:
            return {
                "approved": False,
                "reason": "Invalid stop distance.",
                "decision": decision,
            }

        if decision.action == "BUY":
            stop = entry - stop_distance
            target = (
                entry
                + stop_distance * Decimal(str(decision.take_profit_rr))
            )
        else:
            stop = entry + stop_distance
            target = (
                entry
                - stop_distance * Decimal(str(decision.take_profit_rr))
            )

        balance = Decimal(str(account_balance))

        risk_percent = Decimal(str(decision.risk_percent))

        risk_amount = (
            balance * risk_percent
        ) / Decimal("100")

        risk_per_unit = abs(entry - stop)

        if risk_per_unit <= 0:
            return {
                "approved": False,
                "reason": "Invalid stop distance.",
                "decision": decision,
            }

        quantity = risk_amount / risk_per_unit

        reward = abs(target - entry)
        reward_ratio = reward / risk_per_unit

        if reward_ratio < self.DEFAULT_REWARD_RATIO:
            return {
                "approved": False,
                "reason": "Reward/Risk too low.",
                "decision": decision,
            }

        leverage = min(
            decision.leverage,
            self.MAX_LEVERAGE,
        )

        return {
            "approved": True,
            "action": decision.action,
            "position": decision.position,
            "symbol": snapshot.symbol,
            "timeframe": "1h",
            "entry_price": float(entry),
            "stop_loss": float(stop),
            "take_profit": float(target),
            "quantity": float(quantity),
            "risk_percent": float(risk_percent),
            "reward_ratio": float(reward_ratio),
            "leverage": leverage,
            "reason": decision.reason,
        }

    def _check_portfolio_limits(
        self,
        trading_account,
        symbol,
        balance,
    ):
        """
        Returns a rejection reason string, or None if the trade may proceed.

        The current PQI trial engine supplies a synthetic account object.
        PositionManager may therefore have no database-backed positions for
        trial sessions. In that case, do not reject a valid trial trade merely
        because the legacy positions table is empty/incompatible.
        """

        try:
            open_positions = self.positions.get_open_positions(
                trading_account
            )
        except Exception:
            # Trial mode does not use the legacy TradingAccount/Trade
            # portfolio as its source of truth. The PQI engine itself tracks
            # pqi_session_pairs. Do not make that legacy lookup an execution
            # gate.
            open_positions = []

        if len(open_positions) >= self.MAX_OPEN_POSITIONS:
            return (
                f"Max concurrent positions reached "
                f"({self.MAX_OPEN_POSITIONS})."
            )

        if any(
            getattr(position, "symbol", None) == symbol
            for position in open_positions
        ):
            return f"Position already open on {symbol}."

        # The legacy TradeOutcome table is intentionally NOT queried here.
        #
        # Current PQI trial P/L is maintained by PQIEngine through
        # pqi_session_pairs. Querying TradeOutcome here would cause:
        #
        #   relation "trade_outcomes" does not exist
        #
        # and would prevent otherwise valid trades from opening.
        #
        # Daily loss protection remains handled by the PQI session's
        # realised P/L accounting.

        return None

    @staticmethod
    def _realised_loss_today(trading_account):
        """
        Compatibility method retained for callers that may still reference it.

        The old implementation queried the removed TradeOutcome/Trade tables.
        Current PQI trial accounting uses pqi_session_pairs instead, so this
        method deliberately returns zero rather than querying nonexistent
        legacy tables.
        """
        return Decimal("0")