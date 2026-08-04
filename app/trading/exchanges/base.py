from abc import ABC, abstractmethod


class ExchangeBase(ABC):
    """
    Base contract for every exchange adapter.

    Every Spot/Futures adapter must implement
    exactly the same interface.
    """

    @abstractmethod
    async def connect(self):
        """
        Create or return an authenticated client.
        """
        raise NotImplementedError

    @abstractmethod
    async def validate_credentials(self):
        """
        Validate API credentials.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_account_balance(self):
        """
        Retrieve account balances.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_market_price(
        self,
        symbol: str,
    ):
        """
        Retrieve the latest market price.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_trading_pairs(self):
        """
        Retrieve all tradable symbols.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_symbol_info(
        self,
        symbol: str,
    ):
        """
        Retrieve exchange metadata
        for a trading symbol.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ):
        """
        Retrieve OHLCV candles.
        """
        raise NotImplementedError

    @abstractmethod
    async def place_market_buy(
        self,
        symbol: str,
        quantity: float,
    ):
        """
        Execute a market BUY.
        """
        raise NotImplementedError

    @abstractmethod
    async def place_market_sell(
        self,
        symbol: str,
        quantity: float,
    ):
        """
        Execute a market SELL.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_open_positions(self):
        """
        Retrieve open positions/orders.
        """
        raise NotImplementedError

    @abstractmethod
    async def close_position(
        self,
        symbol: str,
    ):
        """
        Close an existing position.
        """
        raise NotImplementedError