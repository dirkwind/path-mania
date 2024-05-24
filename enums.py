from enum import Enum


class Direction(Enum):
    """Value of each direction corresponds to turtle heading."""

    NORTH = 90
    SOUTH = 270
    EAST = 0
    WEST = 180


class GameState(Enum):
    FROZEN = 0
    PATH = 1
    EVADE = 2


class AbilityState(Enum):
    READY = 0
    CHARGING = 1
    USED = 2
