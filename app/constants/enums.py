from enum import Enum


class UserRole(str, Enum):

    ADMIN = "Admin"

    USER = "User"

    SUPPORT = "Support"


class ExchangeType(str, Enum):

    BINANCE = "Binance"

    BYBIT = "Bybit"


class SubscriptionStatus(str, Enum):

    ACTIVE = "ACTIVE"

    EXPIRED = "EXPIRED"

    CANCELLED = "CANCELLED"


class TradeDirection(str, Enum):

    LONG = "LONG"

    SHORT = "SHORT"


class BotStatus(str, Enum):

    RUNNING = "RUNNING"

    STOPPED = "STOPPED"

    PAUSED = "PAUSED"