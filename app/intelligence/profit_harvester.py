from decimal import Decimal


class ProfitHarvester:
    """
    Manages profitable trades after entry.

    Responsibilities
    ----------------
    • Lock profits
    • Trail stop-loss
    • Exit at target
    • Exit on reversal
    """

    TRAILING_STOP = Decimal("0.01")      # 1%
    BREAKEVEN = Decimal("0.005")         # 0.5%

    def evaluate(
        self,
        position,
        current_price,
        snapshot,
    ):

        entry = Decimal(str(position.entry_price))
        current = Decimal(str(current_price))

        if position.side == "BUY":

            profit = (current - entry) / entry

            if current >= Decimal(str(position.take_profit)):
                return {
                    "action": "CLOSE",
                    "reason": "Take profit reached."
                }

            if profit >= self.BREAKEVEN:

                new_stop = max(
                    Decimal(str(position.stop_loss)),
                    entry
                )

                return {
                    "action": "MOVE_STOP",
                    "stop_loss": float(new_stop),
                    "reason": "Move stop to breakeven."
                }

            if profit >= self.TRAILING_STOP:

                stop = current * Decimal("0.99")

                return {
                    "action": "TRAIL_STOP",
                    "stop_loss": float(stop),
                    "reason": "Trailing stop updated."
                }

            if (
                snapshot.trend == "BEARISH"
                and snapshot.momentum < 0
            ):

                return {
                    "action": "CLOSE",
                    "reason": "Trend reversal detected."
                }

        else:

            profit = (entry - current) / entry

            if current <= Decimal(str(position.take_profit)):
                return {
                    "action": "CLOSE",
                    "reason": "Take profit reached."
                }

            if profit >= self.BREAKEVEN:

                new_stop = min(
                    Decimal(str(position.stop_loss)),
                    entry
                )

                return {
                    "action": "MOVE_STOP",
                    "stop_loss": float(new_stop),
                    "reason": "Move stop to breakeven."
                }

            if profit >= self.TRAILING_STOP:

                stop = current * Decimal("1.01")

                return {
                    "action": "TRAIL_STOP",
                    "stop_loss": float(stop),
                    "reason": "Trailing stop updated."
                }

            if (
                snapshot.trend == "BULLISH"
                and snapshot.momentum > 0
            ):

                return {
                    "action": "CLOSE",
                    "reason": "Trend reversal detected."
                }

        return {
            "action": "HOLD",
            "reason": "Position remains healthy."
        }