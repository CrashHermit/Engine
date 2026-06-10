from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PrecipitationBand(StrEnum):
    HYPER_ARID = "hyper_arid"
    ARID = "arid"
    SEMI_ARID = "semi_arid"
    SUB_HUMID = "sub_humid"
    HUMID = "humid"
    HYPER_HUMID = "hyper_humid"
    SATURATED = "saturated"


@dataclass(frozen=True)
class PrecipitationBandInfo:
    label: str
    description: str
    flavor: list[str]


ORDER: tuple[PrecipitationBand, ...] = (
    PrecipitationBand.HYPER_ARID,
    PrecipitationBand.ARID,
    PrecipitationBand.SEMI_ARID,
    PrecipitationBand.SUB_HUMID,
    PrecipitationBand.HUMID,
    PrecipitationBand.HYPER_HUMID,
    PrecipitationBand.SATURATED,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)

INFO: dict[PrecipitationBand, PrecipitationBandInfo] = {
    PrecipitationBand.HYPER_ARID: PrecipitationBandInfo(
        label="Hyper-arid",
        description="Almost no moisture — dust and distance define the land.",
        flavor=[
            "Cracked earth maps old water.",
            "Plants survive on memory.",
            "Horizons swim in heat haze.",
            "Wind scours without relief.",
            "Rain is a story, not a forecast.",
        ],
    ),
    PrecipitationBand.ARID: PrecipitationBandInfo(
        label="Arid",
        description="Dry country where water is always planned for.",
        flavor=[
            "Wadis lie empty and waiting.",
            "Salt stains the soil.",
            "Clouds pass without gift.",
            "Thirst follows long marches.",
            "Life clusters near seeps.",
        ],
    ),
    PrecipitationBand.SEMI_ARID: PrecipitationBandInfo(
        label="Semi-arid",
        description="Sparse rainfall punctuates long dry spells.",
        flavor=[
            "Grass comes in patches.",
            "Seasonal storms matter greatly.",
            "Wells are marked on every map.",
            "Dust and green trade places.",
            "Sky promises more than it gives.",
        ],
    ),
    PrecipitationBand.SUB_HUMID: PrecipitationBandInfo(
        label="Sub-humid",
        description="Enough rain to sustain steady growth.",
        flavor=[
            "Soil holds moisture after storms.",
            "Streams run part of the year.",
            "Crops succeed with care.",
            "Mornings often feel dew-heavy.",
            "Dry weeks still happen.",
        ],
    ),
    PrecipitationBand.HUMID: PrecipitationBandInfo(
        label="Humid",
        description="Regular rainfall keeps the land green and full.",
        flavor=[
            "Rivers run reliably.",
            "Fungus finds every crevice.",
            "Air feels thick before storms.",
            "Mud follows heavy weather.",
            "Canopies drip long after rain.",
        ],
    ),
    PrecipitationBand.HYPER_HUMID: PrecipitationBandInfo(
        label="Hyper-humid",
        description="Saturated air and frequent downpours.",
        flavor=[
            "Clothes never fully dry.",
            "Mist clings to slopes.",
            "Rot competes with growth.",
            "Thunder becomes background.",
            "Paths turn treacherous quickly.",
        ],
    ),
    PrecipitationBand.SATURATED: PrecipitationBandInfo(
        label="Saturated",
        description="Land drowned in moisture — bogs, floods, and endless wet.",
        flavor=[
            "Water stands in every hollow.",
            "Footing squishes for days.",
            "Mosquitoes own the twilight.",
            "Clouds seem to nest in trees.",
            "Dry ground is rare luxury.",
        ],
    ),
}
