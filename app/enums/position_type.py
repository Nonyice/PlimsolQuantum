from enum import Enum

class PositionType(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"
