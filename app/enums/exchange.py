from enum import Enum


class Exchange(str, Enum):

    BINANCE = "binance"

    BYBIT = "bybit"

    def __str__(self):
        return self.value