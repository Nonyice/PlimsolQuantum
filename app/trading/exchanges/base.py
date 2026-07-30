from abc import ABC, abstractmethod


class ExchangeBase(ABC):
    """Base class for all supported exchanges."""

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def validate_credentials(self):
        pass

    @abstractmethod
    async def get_account_balance(self):
        pass

    @abstractmethod
    async def get_market_price(self, symbol: str):
        pass

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 500
    ):
        pass

    @abstractmethod
    async def place_market_buy(
        self,
        symbol: str,
        quantity: float
    ):
        pass

    @abstractmethod
    async def place_market_sell(
        self,
        symbol: str,
        quantity: float
    ):
        pass

    @abstractmethod
    async def get_open_positions(self):
        pass

    @abstractmethod
    async def close_position(self, symbol: str):
        pass