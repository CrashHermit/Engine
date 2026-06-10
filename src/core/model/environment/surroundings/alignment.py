from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AlignmentBand(StrEnum):
    EVIL = "evil"
    NEUTRAL = "neutral"
    GOOD = "good"


@dataclass(frozen=True)
class AlignmentBandInfo:
    label: str
    description: str
    flavor: list[str]


ORDER: tuple[AlignmentBand, ...] = (
    AlignmentBand.EVIL,
    AlignmentBand.NEUTRAL,
    AlignmentBand.GOOD,
)

BREAKPOINTS: tuple[float, ...] = (1 / 3, 2 / 3)

INFO: dict[AlignmentBand, AlignmentBandInfo] = {
    AlignmentBand.EVIL: AlignmentBandInfo(
        label="Evil",
        description=(
            "Land twisted toward malice. Ordinary creatures share space with "
            "spiteful things, and the air itself feels wrong."
        ),
        flavor=[
            "Shadows cling longer than they should.",
            "Plants wither in patches for no reason.",
            "A chill has nothing to do with weather.",
            "Scavengers grow bold and strange.",
            "Even silence sounds hostile.",
        ],
    ),
    AlignmentBand.NEUTRAL: AlignmentBandInfo(
        label="Neutral",
        description=(
            "Land without moral tint — neither blessed nor cursed. What lives "
            "here follows nature as most folk understand it."
        ),
        flavor=[
            "The ground offers no opinion.",
            "Life and death trade without drama.",
            "Omens feel ordinary.",
            "Ruins are just old, not ominous.",
            "The land watches without judgment.",
        ],
    ),
    AlignmentBand.GOOD: AlignmentBandInfo(
        label="Good",
        description=(
            "Land inclined toward gentleness. Creatures tend toward the shy and "
            "wondrous, and the country feels faintly welcoming."
        ),
        flavor=[
            "Light seems a little warmer.",
            "Wild things startle easily, not savagely.",
            "Water tastes clean without effort.",
            "Flowers appear where none were planted.",
            "Rest comes easier at camp.",
        ],
    ),
}
