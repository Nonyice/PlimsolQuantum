from enum import Enum


class MarketType(str, Enum):
    SPOT = "spot"
    FUTURES = "futures"

    def __str__(self):
        return self.value