from datetime import datetime
from decimal import Decimal

from app.enums.exit_reason import ExitReason
from app.enums.trade_status import TradeStatus
from app.extensions import db

from app.models.trade import Trade
from app.models.trade_outcome import TradeOutcome

from app.services.public_market_service import PublicMarketService

from app.trading.position_manager import PositionManager
from app.trading.trade_executor import TradeExecutor


class PositionMonitor:
    """
    Watches every OPEN position for a trading account and closes any that
    have hit their stop-loss or take-profit.

    Before this existed, RiskGuardian computed a stop_loss/take_profit for
    every trade but nothing in the app ever acted on those numbers, and no
    exchange order carried a bracket/OCO leg either - a filled position had
    no protection at all and could only be closed manually. This runs once
    per trading cycle, ahead of any new-trade evaluation, so exits always
    take priority over opening new risk.
    """

    def __init__(self):
        self.positions = PositionManager()
        self.executor = TradeExecutor()

    async def check_exits(self, exchange, trading_account):
        open_positions = self.positions.get_open_positions(trading_account)

        closed = []

        for position in open_positions:
            try:
                price = await self._current_price(trading_account, position.symbol)
            except Exception:
                # Data hiccup for this symbol - don't block the rest of the
                # scan, retry next tick.
                continue

            exit_reason = self._hit(position, price)

            if exit_reason is None:
                continue

            result = await self.executor.close_position(
                exchange=exchange,
                trading_account=trading_account,
                symbol=position.symbol,
                exit_price=price,
                exit_reason=exit_reason,
            )

            self._record_outcome(trading_account, position, price, exit_reason)

            closed.append({"symbol": position.symbol, "reason": exit_reason.value, "result": result})

        return closed

    @staticmethod
    def _hit(position, price):
        price = Decimal(str(price))
        stop = Decimal(str(position.stop_loss))
        target = Decimal(str(position.take_profit))

        if position.side == "BUY":
            if price <= stop:
                return ExitReason.STOP_LOSS
            if price >= target:
                return ExitReason.TAKE_PROFIT
        else:
            if price >= stop:
                return ExitReason.STOP_LOSS
            if price <= target:
                return ExitReason.TAKE_PROFIT

        return None

    @staticmethod
    async def _current_price(trading_account, symbol):
        ticker = await PublicMarketService.ticker(
            exchange=trading_account.exchange.value,
            market_type=trading_account.market_type.value,
            symbol=symbol,
        )
        return ticker["last"]

    @staticmethod
    def _record_outcome(trading_account, position, exit_price, exit_reason):
        trade = (
            Trade.query
            .filter_by(
                trading_account_id=trading_account.id,
                symbol=position.symbol,
                status=TradeStatus.CLOSED,
            )
            .order_by(Trade.opened_at.desc())
            .first()
        )

        if trade is None or trade.outcome is not None:
            return

        entry = Decimal(str(position.entry_price))
        exit_ = Decimal(str(exit_price))
        quantity = Decimal(str(position.quantity))

        gross = (
            (exit_ - entry) * quantity
            if position.side == "BUY"
            else (entry - exit_) * quantity
        )

        risk_per_unit = abs(entry - Decimal(str(position.stop_loss)))
        reward_risk = (
            abs(gross / quantity) / risk_per_unit
            if quantity and risk_per_unit
            else Decimal("0")
        )

        outcome = TradeOutcome(
            trade_id=trade.id,
            exit_price=exit_,
            gross_profit=gross,
            net_profit=gross,  # fees/slippage not modelled by any exchange adapter yet
            fees=Decimal("0"),
            slippage=Decimal("0"),
            reward_risk=reward_risk,
            drawdown=Decimal("0"),
            duration_minutes=int((datetime.utcnow() - trade.opened_at).total_seconds() // 60),
            win=gross > 0,
            exit_reason=exit_reason,
            closed_at=datetime.utcnow(),
        )

        db.session.add(outcome)
        db.session.commit()
