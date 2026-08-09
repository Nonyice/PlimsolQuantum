from app.enums.exchange import Exchange
from app.enums.market import MarketType

from app.extensions import db
from app.models.base import BaseModel


class TradingAccount(BaseModel):
    """
    Stores a user's connected exchange account.

    PQI does not hold trading funds.
    Balances and trading capital are fetched from
    the connected exchange.
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

    # Encrypted credentials.
    api_key = db.Column(
        db.Text,
        nullable=False,
    )

    api_secret = db.Column(
        db.Text,
        nullable=False,
    )

    # Used by exchanges such as OKX.
    passphrase = db.Column(
        db.Text,
        nullable=True,
    )

    is_testnet = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
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

    is_default = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    can_trade = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    last_sync = db.Column(
        db.DateTime,
        nullable=True,
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
            f"name='{self.account_name}')>"
        )