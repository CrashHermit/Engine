from dataclasses import dataclass
from enum import StrEnum


class WindDirectionEnum(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTH_EAST = "north_east"
    NORTH_WEST = "north_west"
    SOUTH_EAST = "south_east"
    SOUTH_WEST = "south_west"

@dataclass
class WindDirectionData:
    wind_direction: WindDirectionEnum