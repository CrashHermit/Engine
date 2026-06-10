from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WindIntensityBand(StrEnum):
    CALM = "calm"
    GENTLE = "gentle"
    BREEZY = "breezy"
    BLUSTERY = "blustery"
    GALE = "gale"
    STORM = "storm"
    HURRICANE = "hurricane"


@dataclass(frozen=True)
class WindIntensityBandInfo:
    label: str
    description: str
    flavor: list[str]


ORDER: tuple[WindIntensityBand, ...] = (
    WindIntensityBand.CALM,
    WindIntensityBand.GENTLE,
    WindIntensityBand.BREEZY,
    WindIntensityBand.BLUSTERY,
    WindIntensityBand.GALE,
    WindIntensityBand.STORM,
    WindIntensityBand.HURRICANE,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)

INFO: dict[WindIntensityBand, WindIntensityBandInfo] = {
    WindIntensityBand.CALM: WindIntensityBandInfo(
        label="Calm",
        description="Still air — smoke rises straight.",
        flavor=[
            "Flags hang limp.",
            "Insects drone nearby.",
            "Ash drifts upward.",
            "Sound carries far.",
            "Dust settles where it falls.",
        ],
    ),
    WindIntensityBand.GENTLE: WindIntensityBandInfo(
        label="Gentle",
        description="A light stir that moves scent and leaf.",
        flavor=[
            "Grass whispers.",
            "Cloth flutters softly.",
            "Ripples cross still water.",
            "Chimney smoke bends slightly.",
            "Hair shifts at the temples.",
        ],
    ),
    WindIntensityBand.BREEZY: WindIntensityBandInfo(
        label="Breezy",
        description="Steady wind that tugs at loose things.",
        flavor=[
            "Branches sway in rhythm.",
            "Loose grit skitters.",
            "Cloaks need securing.",
            "Birds tilt into gusts.",
            "Doors sigh in frames.",
        ],
    ),
    WindIntensityBand.BLUSTERY: WindIntensityBandInfo(
        label="Blustery",
        description="Gusty wind that demands attention.",
        flavor=[
            "Gusts arrive in bursts.",
            "Eyes water outdoors.",
            "Hats need holding.",
            "Dust devils spin up.",
            "Speech competes with noise.",
        ],
    ),
    WindIntensityBand.GALE: WindIntensityBandInfo(
        label="Gale",
        description="Strong wind that tests footing and structure.",
        flavor=[
            "Walking leans into force.",
            "Branches crack overhead.",
            "Loose objects become hazards.",
            "Rain drives sideways.",
            "Animals seek shelter.",
        ],
    ),
    WindIntensityBand.STORM: WindIntensityBandInfo(
        label="Storm",
        description="Violent wind that reshapes the moment.",
        flavor=[
            "Debris scours the air.",
            "Standing upright is work.",
            "Structures groan.",
            "Light fails between gusts.",
            "Fear feels reasonable.",
        ],
    ),
    WindIntensityBand.HURRICANE: WindIntensityBandInfo(
        label="Hurricane",
        description="Devastating wind that owns the landscape.",
        flavor=[
            "Nothing exposed is safe.",
            "Sound becomes a roar.",
            "Stone seems to tremble.",
            "Visibility collapses.",
            "Survival is the only task.",
        ],
    ),
}
