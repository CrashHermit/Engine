from __future__ import annotations

from enum import StrEnum


class WindDirectionBand(StrEnum):
    NORTH = "north"
    NORTH_EAST = "north_east"
    EAST = "east"
    SOUTH_EAST = "south_east"
    SOUTH = "south"
    SOUTH_WEST = "south_west"
    WEST = "west"
    NORTH_WEST = "north_west"


ORDER: tuple[WindDirectionBand, ...] = (
    WindDirectionBand.NORTH,
    WindDirectionBand.NORTH_EAST,
    WindDirectionBand.EAST,
    WindDirectionBand.SOUTH_EAST,
    WindDirectionBand.SOUTH,
    WindDirectionBand.SOUTH_WEST,
    WindDirectionBand.WEST,
    WindDirectionBand.NORTH_WEST,
)

BREAKPOINTS: tuple[float, ...] = (1 / 8, 2 / 8, 3 / 8, 4 / 8, 5 / 8, 6 / 8, 7 / 8,)
