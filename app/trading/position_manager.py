from app.extensions import db
from app.models.position import Position


class PositionManager:
    """
    Manages all open positions.

    Prevents duplicate trades and
    tracks every live position.
    """

    def get_open_positions(
        self,
        trading_account,
    ):

        return Position.query.filter_by(
            trading_account_id=trading_account.id,
            status="OPEN",
        ).all()

    def get_position(
        self,
        trading_account,
        symbol,
    ):

        return Position.query.filter_by(
            trading_account_id=trading_account.id,
            symbol=symbol,
            status="OPEN",
        ).first()

    def has_open_position(
        self,
        trading_account,
        symbol,
    ):

        return (
            self.get_position(
                trading_account,
                symbol,
            )
            is not None
        )

    def open_position(
        self,
        trading_account,
        execution,
    ):

        position = Position(
            trading_account_id=trading_account.id,
            symbol=execution["symbol"],
            side=execution["action"],
            quantity=execution["quantity"],
            entry_price=execution["entry_price"],
            stop_loss=execution["stop_loss"],
            take_profit=execution["take_profit"],
            status="OPEN",
        )

        db.session.add(position)
        db.session.commit()

        return position

    def close_position(
        self,
        position,
        exit_price,
    ):

        position.exit_price = exit_price
        position.status = "CLOSED"

        db.session.commit()