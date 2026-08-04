from decimal import Decimal

from app.enums.exchange import Exchange
from app.enums.market_type import MarketType
from app.extensions import db
from app.models.base import BaseModel


class TradingAccount(BaseModel):
    """
    Stores a user's trading account configuration.

    A user can connect multiple exchange accounts,
    e.g. Binance Spot, Binance Futures, Bybit, OKX, etc.
    """

    __tablename__ = "trading_accounts"

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    account_name = db.Column(
        db.String(100),
        nullable=False,
    )

    exchange = db.Column(
        db.Enum(Exchange),
        nullable=False,
        index=True,
    )

    market_type = db.Column(
        db.Enum(MarketType),
        nullable=False,
        default=MarketType.SPOT,
        index=True,
    )

    api_key = db.Column(
        db.Text,
        nullable=False,
    )

    api_secret = db.Column(
        db.Text,
        nullable=False,
    )

    symbol = db.Column(
        db.String(20),
        nullable=False,
        default="BTCUSDT",
    )

    leverage = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    is_testnet = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    trading_capital = db.Column(
        db.Numeric(18, 8),
        nullable=False,
        default=Decimal("10.00000000"),
    )

    max_concurrent_trades = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    user = db.relationship(
        "User",
        back_populates="trading_accounts",
        lazy="select",
    )

    @property
    def is_spot(self):
        return self.market_type == MarketType.SPOT

    @property
    def is_futures(self):
        return self.market_type == MarketType.FUTURES

    def __repr__(self):
        return (
            f"<TradingAccount("
            f"id={self.id}, "
            f"user={self.user_id}, "
            f"exchange={self.exchange.value}, "
            f"market={self.market_type.value}, "
            f"symbol='{self.symbol}', "
            f"name='{self.account_name}')>"
        )