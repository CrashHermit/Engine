from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class WindDirectionBandInfo:
    label: str
    description: str
    flavor: list[str]


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

BREAKPOINTS: tuple[float, ...] = (
    1 / 8,
    2 / 8,
    3 / 8,
    4 / 8,
    5 / 8,
    6 / 8,
    7 / 8,
)

INFO: dict[WindDirectionBand, WindDirectionBandInfo] = {
    WindDirectionBand.NORTH: WindDirectionBandInfo(
        label="North",
        description="Wind from the north.",
        flavor=[
            "Cold air pushes from the poleward quarter.",
            "Banners stream toward the south.",
            "Smoke drifts southward.",
            "The wind comes from over your shoulder if you face south.",
            "Northern gusts carry distant chill.",
        ],
    ),
    WindDirectionBand.NORTH_EAST: WindDirectionBandInfo(
        label="North-east",
        description="Wind from the north-east.",
        flavor=[
            "A diagonal push from the north and east.",
            "Dust trails toward the south-west.",
            "Sailors would call it a quartering wind.",
            "Leaves skitter south-west across the ground.",
            "The air arrives from your right if you face north.",
        ],
    ),
    WindDirectionBand.EAST: WindDirectionBandInfo(
        label="East",
        description="Wind from the east.",
        flavor=[
            "Air flows from the rising sun's quarter.",
            "Long westward streaks mark blown sand.",
            "Hair pulls toward the west.",
            "The wind meets you if you walk east.",
            "Morning weather often rides this bearing.",
        ],
    ),
    WindDirectionBand.SOUTH_EAST: WindDirectionBandInfo(
        label="South-east",
        description="Wind from the south-east.",
        flavor=[
            "Warm and damp air often comes from this bearing.",
            "Rain sometimes announces itself early.",
            "Flags lift toward the north-west.",
            "A diagonal press from sunward lowlands.",
            "Scent travels north-west on the gusts.",
        ],
    ),
    WindDirectionBand.SOUTH: WindDirectionBandInfo(
        label="South",
        description="Wind from the south.",
        flavor=[
            "Warmer air pushes from the equatorward quarter.",
            "Snow drifts north on open ground.",
            "Cloaks bell toward the north.",
            "The wind at your back if you face north.",
            "Southern gusts feel broader and softer.",
        ],
    ),
    WindDirectionBand.SOUTH_WEST: WindDirectionBandInfo(
        label="South-west",
        description="Wind from the south-west.",
        flavor=[
            "A common bearing for long storms.",
            "Clouds often march from this quarter.",
            "Spray flies north-east off water.",
            "Diagonal gusts test footing.",
            "Mariners watch this bearing with care.",
        ],
    ),
    WindDirectionBand.WEST: WindDirectionBandInfo(
        label="West",
        description="Wind from the west.",
        flavor=[
            "Air flows from the setting sun's quarter.",
            "Long eastward streaks mark blown grit.",
            "Doors on the east side strain in latches.",
            "The wind meets you if you walk west.",
            "Evening weather often follows this bearing.",
        ],
    ),
    WindDirectionBand.NORTH_WEST: WindDirectionBandInfo(
        label="North-west",
        description="Wind from the north-west.",
        flavor=[
            "Sharp, clean gusts from the cold quarter.",
            "Clear skies often follow a north-wester.",
            "Flags stream toward the south-east.",
            "A biting diagonal from pole and sunset.",
            "Birds tuck on the lee side to the south-east.",
        ],
    ),
}
