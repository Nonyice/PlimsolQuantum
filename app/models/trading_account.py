from __future__ import annotations

from app.enums.exchange import Exchange
from app.enums.market import MarketType

from app.extensions import db
from app.models.base import BaseModel
from app.security.encryption import (
    encrypt_value,
    decrypt_value,
)


class TradingAccount(BaseModel):
    """
    Stores a user's connected exchange account.

    PQI does not hold trading funds.
    Balances and trading capital are fetched from
    the connected exchange.

    Exchange credentials are encrypted before being
    stored in the database.
    """

    __tablename__ = "trading_accounts"

    # ==========================================================
    # USER
    # ==========================================================

    user_id = db.Column(
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ==========================================================
    # ACCOUNT
    # ==========================================================

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

    # ==========================================================
    # ENCRYPTED EXCHANGE CREDENTIALS
    # ==========================================================

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

    # ==========================================================
    # EXCHANGE CONFIGURATION
    # ==========================================================

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

    # ==========================================================
    # ACCOUNT STATUS
    # ==========================================================

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

    # IMPORTANT:
    #
    # Connecting an exchange does NOT automatically authorize
    # PQI to trade.
    #
    # This remains False until the appropriate live-trading
    # checks and authorization have been completed.
    #
    can_trade = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
    )

    # ==========================================================
    # SYNCHRONIZATION
    # ==========================================================

    last_sync = db.Column(
        db.DateTime,
        nullable=True,
    )

    # ==========================================================
    # TIMESTAMPS
    # ==========================================================

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

    # ==========================================================
    # RELATIONSHIP
    # ==========================================================

    user = db.relationship(
        "User",
        back_populates="trading_accounts",
        lazy="select",
    )

    # ==========================================================
    # CREDENTIAL ENCRYPTION
    # ==========================================================

    def set_credentials(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str | None = None,
    ) -> None:
        """
        Encrypt exchange credentials before storing them.
        """

        if not api_key:
            raise ValueError(
                "API key cannot be empty."
            )

        if not api_secret:
            raise ValueError(
                "API secret cannot be empty."
            )

        self.api_key = encrypt_value(
            api_key.strip()
        )

        self.api_secret = encrypt_value(
            api_secret.strip()
        )

        if passphrase:
            self.passphrase = encrypt_value(
                passphrase.strip()
            )
        else:
            self.passphrase = None

    # ==========================================================
    # CREDENTIAL DECRYPTION
    # ==========================================================

    def get_credentials(self) -> dict:
        """
        Decrypt exchange credentials when PQI needs to
        communicate with the exchange.

        Never expose the returned values to templates,
        logs, browser responses, or Flask sessions.
        """

        return {
            "api_key": decrypt_value(
                self.api_key
            ),
            "api_secret": decrypt_value(
                self.api_secret
            ),
            "passphrase": (
                decrypt_value(self.passphrase)
                if self.passphrase
                else None
            ),
        }

    # ==========================================================
    # MARKET HELPERS
    # ==========================================================

    @property
    def is_spot(self) -> bool:
        return (
            self.market_type
            == MarketType.SPOT
        )

    @property
    def is_futures(self) -> bool:
        return (
            self.market_type
            == MarketType.FUTURES
        )

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self) -> str:
        exchange_name = (
            self.exchange.value
            if self.exchange
            else "unknown"
        )

        market_name = (
            self.market_type.value
            if self.market_type
            else "unknown"
        )

        return (
            f"<TradingAccount("
            f"id={self.id}, "
            f"user={self.user_id}, "
            f"exchange={exchange_name}, "
            f"market={market_name}, "
            f"name='{self.account_name}')>"
        )