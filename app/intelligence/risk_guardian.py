from decimal import Decimal


class RiskGuardian:

    DEFAULT_RISK_PERCENT = Decimal("2.0")
    DEFAULT_REWARD_RATIO = Decimal("2.0")
    MAX_LEVERAGE = 20

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

        tf = snapshot.timeframes["1h"]

        indicators = tf.indicators

        entry = Decimal(str(snapshot.ticker["lastPrice"]))

        atr = Decimal(str(indicators.atr))

        stop_distance = (
            atr *
            Decimal(str(decision.stop_multiplier))
        )

        if decision.action == "BUY":

            stop = entry - stop_distance

            target = (
                entry +
                stop_distance *
                Decimal(str(decision.take_profit_rr))
            )

        else:

            stop = entry + stop_distance

            target = (
                entry -
                stop_distance *
                Decimal(str(decision.take_profit_rr))
            )

        balance = Decimal(str(account_balance))

        risk_percent = Decimal(
            str(decision.risk_percent)
        )

        risk_amount = (
            balance *
            risk_percent
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