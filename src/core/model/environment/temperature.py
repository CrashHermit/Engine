from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TemperatureBand(StrEnum):
    FRIGID = "frigid"
    FREEZING = "freezing"
    COOL = "cool"
    MILD = "mild"
    WARM = "warm"
    HOT = "hot"
    SCORCHING = "scorching"


@dataclass(frozen=True)
class TemperatureBandInfo:
    label: str
    description: str
    flavor: list[str]


ORDER: tuple[TemperatureBand, ...] = (
    TemperatureBand.FRIGID,
    TemperatureBand.FREEZING,
    TemperatureBand.COOL,
    TemperatureBand.MILD,
    TemperatureBand.WARM,
    TemperatureBand.HOT,
    TemperatureBand.SCORCHING,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)

INFO: dict[TemperatureBand, TemperatureBandInfo] = {
    TemperatureBand.FRIGID: TemperatureBandInfo(
        label="Frigid",
        description="Air that bites and burns the lungs.",
        flavor=[
            "Breath clouds and vanishes.",
            "Metal sticks to bare skin.",
            "Ice forms in shadowed cracks.",
            "Sound carries sharp and thin.",
            "Fingers numb within minutes.",
        ],
    ),
    TemperatureBand.FREEZING: TemperatureBandInfo(
        label="Freezing",
        description="Persistent cold that shapes every choice outdoors.",
        flavor=[
            "Ground crunches underfoot.",
            "Water skins over by morning.",
            "Exposed flesh aches quickly.",
            "Frost feathers the grass.",
            "Warm layers feel mandatory.",
        ],
    ),
    TemperatureBand.COOL: TemperatureBandInfo(
        label="Cool",
        description="Brisk air that keeps you alert without constant struggle.",
        flavor=[
            "A jacket feels right.",
            "Cheeks pink in the wind.",
            "Mornings stay damp and sharp.",
            "Sun warmth is welcome, not fierce.",
            "Steam rises where heat meets cold.",
        ],
    ),
    TemperatureBand.MILD: TemperatureBandInfo(
        label="Mild",
        description="Comfortable temperatures that neither punish nor pamper.",
        flavor=[
            "Work outdoors feels sustainable.",
            "Layers come off by midday.",
            "Evenings cool gently.",
            "Seasons announce themselves softly.",
            "Neither heat nor chill dominates.",
        ],
    ),
    TemperatureBand.WARM: TemperatureBandInfo(
        label="Warm",
        description="Heat that presses close and slows the unhurried.",
        flavor=[
            "Shade becomes valuable.",
            "Dust and pollen hang in the air.",
            "Cloth clings after effort.",
            "Insects grow bolder.",
            "Water tastes better than wine.",
        ],
    ),
    TemperatureBand.HOT: TemperatureBandInfo(
        label="Hot",
        description="Heavy heat that drains stamina and demands rhythm.",
        flavor=[
            "Sunlight feels like weight.",
            "Mirages shimmer on stone.",
            "Sweat dries before it cools.",
            "Midday stills most movement.",
            "Metal burns to the touch.",
        ],
    ),
    TemperatureBand.SCORCHING: TemperatureBandInfo(
        label="Scorching",
        description="Oppressive heat that threatens the careless.",
        flavor=[
            "Air shimmers above baked earth.",
            "Shade offers only partial mercy.",
            "Thirst arrives without warning.",
            "Skin reddens in minutes.",
            "The world feels baked still.",
        ],
    ),
}
