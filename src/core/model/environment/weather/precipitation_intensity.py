from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.core.model.environment.weather.cloud_cover import CloudCoverBand
from src.core.model.environment.weather.humidity import HumidityBand


class PrecipitationIntensityBand(StrEnum):
    NONE = "none"
    DRIZZLE = "drizzle"
    LIGHT = "light"
    STEADY = "steady"
    HEAVY = "heavy"
    TORRENTIAL = "torrential"
    CLOUDBURST = "cloudburst"


@dataclass(frozen=True)
class PrecipitationIntensityBandInfo:
    label: str
    description: str
    flavor: list[str]


ORDER: tuple[PrecipitationIntensityBand, ...] = (
    PrecipitationIntensityBand.NONE,
    PrecipitationIntensityBand.DRIZZLE,
    PrecipitationIntensityBand.LIGHT,
    PrecipitationIntensityBand.STEADY,
    PrecipitationIntensityBand.HEAVY,
    PrecipitationIntensityBand.TORRENTIAL,
    PrecipitationIntensityBand.CLOUDBURST,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)

INFO: dict[PrecipitationIntensityBand, PrecipitationIntensityBandInfo] = {
    PrecipitationIntensityBand.NONE: PrecipitationIntensityBandInfo(
        label="None",
        description="No falling precipitation.",
        flavor=[
            "Ground stays as it was.",
            "Sky may still threaten.",
            "Dust remains airborne.",
            "Footsteps sound normal.",
            "Gear stays dry.",
        ],
    ),
    PrecipitationIntensityBand.DRIZZLE: PrecipitationIntensityBandInfo(
        label="Drizzle",
        description="Fine, persistent mist.",
        flavor=[
            "Moisture beads on hair.",
            "Stone darkens slowly.",
            "Umbrellas seem excessive.",
            "Paths turn slick over time.",
            "Mood turns inward.",
        ],
    ),
    PrecipitationIntensityBand.LIGHT: PrecipitationIntensityBandInfo(
        label="Light",
        description="Gentle rain or snow that patters softly.",
        flavor=[
            "Rhythm on roofs soothes.",
            "Puddles form in low spots.",
            "Scent of wet earth rises.",
            "Visibility holds.",
            "Cloaks darken at the hem.",
        ],
    ),
    PrecipitationIntensityBand.STEADY: PrecipitationIntensityBandInfo(
        label="Steady",
        description="Continuous fall that soaks through patience.",
        flavor=[
            "Streams rise audibly.",
            "Boots squelch by afternoon.",
            "Fires struggle outdoors.",
            "Conversation moves indoors.",
            "The world softens.",
        ],
    ),
    PrecipitationIntensityBand.HEAVY: PrecipitationIntensityBandInfo(
        label="Heavy",
        description="Hard rain or snow that reshapes plans.",
        flavor=[
            "Drains overflow.",
            "Hearing narrows to weather.",
            "Travel slows sharply.",
            "Cold finds every gap.",
            "Umbrellas invert.",
        ],
    ),
    PrecipitationIntensityBand.TORRENTIAL: PrecipitationIntensityBandInfo(
        label="Torrential",
        description="Violent downpour — visibility and footing suffer.",
        flavor=[
            "Sheets of water blur sight.",
            "Floods form in minutes.",
            "Thunder may accompany.",
            "Shelter becomes urgent.",
            "Dry cloth is fantasy.",
        ],
    ),
    PrecipitationIntensityBand.CLOUDBURST: PrecipitationIntensityBandInfo(
        label="Cloudburst",
        description="Catastrophic rainfall in a short span.",
        flavor=[
            "The sky seems to empty.",
            "Gullies become rivers.",
            "Stone channels roar.",
            "Exposure risks drowning.",
            "Aftermath mud everywhere.",
        ],
    ),
}

INTENSITY_GRID: dict[
    tuple[CloudCoverBand, HumidityBand], PrecipitationIntensityBand
] = {
        # â”€â”€ CLEAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (CloudCoverBand.CLEAR, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.CLEAR, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.CLEAR, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.CLEAR, HumidityBand.MILD): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.CLEAR, HumidityBand.HUMID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.CLEAR, HumidityBand.MUGGY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.CLEAR, HumidityBand.SOAKING): PrecipitationIntensityBand.NONE,
        # â”€â”€ FEW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (CloudCoverBand.FEW, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.FEW, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.FEW, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.FEW, HumidityBand.MILD): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.FEW, HumidityBand.HUMID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.FEW, HumidityBand.MUGGY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.FEW, HumidityBand.SOAKING): PrecipitationIntensityBand.NONE,
        # â”€â”€ SCATTERED â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (CloudCoverBand.SCATTERED, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.SCATTERED, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.SCATTERED, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.SCATTERED, HumidityBand.MILD): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.SCATTERED, HumidityBand.HUMID): PrecipitationIntensityBand.NONE,
        (
            CloudCoverBand.SCATTERED,
            HumidityBand.MUGGY,
        ): PrecipitationIntensityBand.DRIZZLE,
        (
            CloudCoverBand.SCATTERED,
            HumidityBand.SOAKING,
        ): PrecipitationIntensityBand.LIGHT,
        # â”€â”€ BROKEN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (CloudCoverBand.BROKEN, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.BROKEN, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.BROKEN, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.BROKEN, HumidityBand.MILD): PrecipitationIntensityBand.DRIZZLE,
        (CloudCoverBand.BROKEN, HumidityBand.HUMID): PrecipitationIntensityBand.LIGHT,
        (CloudCoverBand.BROKEN, HumidityBand.MUGGY): PrecipitationIntensityBand.LIGHT,
        (
            CloudCoverBand.BROKEN,
            HumidityBand.SOAKING,
        ): PrecipitationIntensityBand.STEADY,
        # â”€â”€ MOSTLY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (CloudCoverBand.MOSTLY, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.MOSTLY, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.MOSTLY, HumidityBand.CRISP): PrecipitationIntensityBand.DRIZZLE,
        (CloudCoverBand.MOSTLY, HumidityBand.MILD): PrecipitationIntensityBand.LIGHT,
        (CloudCoverBand.MOSTLY, HumidityBand.HUMID): PrecipitationIntensityBand.STEADY,
        (CloudCoverBand.MOSTLY, HumidityBand.MUGGY): PrecipitationIntensityBand.STEADY,
        (CloudCoverBand.MOSTLY, HumidityBand.SOAKING): PrecipitationIntensityBand.HEAVY,
        # â”€â”€ OVERCAST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (CloudCoverBand.OVERCAST, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.OVERCAST, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
        (
            CloudCoverBand.OVERCAST,
            HumidityBand.CRISP,
        ): PrecipitationIntensityBand.DRIZZLE,
        (CloudCoverBand.OVERCAST, HumidityBand.MILD): PrecipitationIntensityBand.LIGHT,
        (CloudCoverBand.OVERCAST, HumidityBand.HUMID): PrecipitationIntensityBand.HEAVY,
        (CloudCoverBand.OVERCAST, HumidityBand.MUGGY): PrecipitationIntensityBand.HEAVY,
        (
            CloudCoverBand.OVERCAST,
            HumidityBand.SOAKING,
        ): PrecipitationIntensityBand.TORRENTIAL,
        # â”€â”€ LEADEN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        (CloudCoverBand.LEADEN, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.LEADEN, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
        (CloudCoverBand.LEADEN, HumidityBand.CRISP): PrecipitationIntensityBand.DRIZZLE,
        (CloudCoverBand.LEADEN, HumidityBand.MILD): PrecipitationIntensityBand.STEADY,
        (CloudCoverBand.LEADEN, HumidityBand.HUMID): PrecipitationIntensityBand.HEAVY,
        (
            CloudCoverBand.LEADEN,
            HumidityBand.MUGGY,
        ): PrecipitationIntensityBand.TORRENTIAL,
        (
            CloudCoverBand.LEADEN,
            HumidityBand.SOAKING,
        ): PrecipitationIntensityBand.CLOUDBURST,
    }
