from enum import IntEnum, auto


class JoinType(IntEnum):
    JOIN_INNER = 0
    JOIN_LEFT = auto()
    JOIN_FULL = auto()
    JOIN_RIGHT = auto()
    JOIN_SEMI = auto()
    JOIN_ANTI = auto()
    JOIN_RIGHT_ANTI = auto()
    JOIN_UNIQUE_OUTER = auto()
    JOIN_UNIQUE_INNER = auto()
