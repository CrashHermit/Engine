from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HumidityBand(StrEnum):
    ARID = "arid"
    DRY = "dry"
    CRISP = "crisp"
    MILD = "mild"
    HUMID = "humid"
    MUGGY = "muggy"
    SOAKING = "soaking"


@dataclass(frozen=True)
class HumidityBandInfo:
    label: str
    description: str
    flavor: list[str]


ORDER: tuple[HumidityBand, ...] = (
    HumidityBand.ARID,
    HumidityBand.DRY,
    HumidityBand.CRISP,
    HumidityBand.MILD,
    HumidityBand.HUMID,
    HumidityBand.MUGGY,
    HumidityBand.SOAKING,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)

INFO: dict[HumidityBand, HumidityBandInfo] = {
    HumidityBand.ARID: HumidityBandInfo(
        label="Arid",
        description="Bone-dry air that pulls moisture from everything.",
        flavor=[
            "Lips crack without notice.",
            "Static sparks at touch.",
            "Wood shrinks and creaks.",
            "Thirst arrives quickly.",
            "Skin feels tight.",
        ],
    ),
    HumidityBand.DRY: HumidityBandInfo(
        label="Dry",
        description="Low humidity — crisp and thirsty.",
        flavor=[
            "Nights cool sharply.",
            "Dust hangs after disturbance.",
            "Fabric dries fast.",
            "Breath feels clean.",
            "Plants wilt without water.",
        ],
    ),
    HumidityBand.CRISP: HumidityBandInfo(
        label="Crisp",
        description="Fresh air with comfortable dryness.",
        flavor=[
            "Mornings feel clean.",
            "Scents carry clearly.",
            "Sweat evaporates quickly.",
            "Sky looks sharper.",
            "Energy feels easy.",
        ],
    ),
    HumidityBand.MILD: HumidityBandInfo(
        label="Mild",
        description="Balanced moisture — neither parched nor sodden.",
        flavor=[
            "Comfortable for long work.",
            "Skin feels neutral.",
            "Fog is uncommon.",
            "Seasons feel moderate.",
            "Air supports steady effort.",
        ],
    ),
    HumidityBand.HUMID: HumidityBandInfo(
        label="Humid",
        description="Moist air that clings and softens edges.",
        flavor=[
            "Hair refuses to behave.",
            "Stone sweats indoors.",
            "Smells grow stronger.",
            "Cloth sticks subtly.",
            "Storms brew more easily.",
        ],
    ),
    HumidityBand.MUGGY: HumidityBandInfo(
        label="Muggy",
        description="Heavy, oppressive moisture.",
        flavor=[
            "Breathing feels thick.",
            "Insects thrive.",
            "Shade offers little relief.",
            "Effort costs more.",
            "Everything smells alive.",
        ],
    ),
    HumidityBand.SOAKING: HumidityBandInfo(
        label="Soaking",
        description="Air nearly saturated — sweat cannot cool.",
        flavor=[
            "Dripping leaves never dry.",
            "Paper warps in pockets.",
            "Rust advances overnight.",
            "Mold finds every corner.",
            "Dry is a memory.",
        ],
    ),
}
