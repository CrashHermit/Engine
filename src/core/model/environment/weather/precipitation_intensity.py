from __future__ import annotations

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

INTENSITY_GRID: dict[
    tuple[CloudCoverBand, HumidityBand], PrecipitationIntensityBand
] = {
    # -- CLEAR --
    (CloudCoverBand.CLEAR, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.CLEAR, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.CLEAR, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.CLEAR, HumidityBand.MILD): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.CLEAR, HumidityBand.HUMID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.CLEAR, HumidityBand.MUGGY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.CLEAR, HumidityBand.SOAKING): PrecipitationIntensityBand.NONE,
    # -- FEW --
    (CloudCoverBand.FEW, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.FEW, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.FEW, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.FEW, HumidityBand.MILD): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.FEW, HumidityBand.HUMID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.FEW, HumidityBand.MUGGY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.FEW, HumidityBand.SOAKING): PrecipitationIntensityBand.NONE,
    # -- SCATTERED --
    (CloudCoverBand.SCATTERED, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.SCATTERED, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.SCATTERED, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.SCATTERED, HumidityBand.MILD): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.SCATTERED, HumidityBand.HUMID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.SCATTERED, HumidityBand.MUGGY): PrecipitationIntensityBand.DRIZZLE,
    (CloudCoverBand.SCATTERED, HumidityBand.SOAKING): PrecipitationIntensityBand.LIGHT,
    # -- BROKEN --
    (CloudCoverBand.BROKEN, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.BROKEN, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.BROKEN, HumidityBand.CRISP): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.BROKEN, HumidityBand.MILD): PrecipitationIntensityBand.DRIZZLE,
    (CloudCoverBand.BROKEN, HumidityBand.HUMID): PrecipitationIntensityBand.LIGHT,
    (CloudCoverBand.BROKEN, HumidityBand.MUGGY): PrecipitationIntensityBand.LIGHT,
    (CloudCoverBand.BROKEN, HumidityBand.SOAKING): PrecipitationIntensityBand.STEADY,
    # -- MOSTLY --
    (CloudCoverBand.MOSTLY, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.MOSTLY, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.MOSTLY, HumidityBand.CRISP): PrecipitationIntensityBand.DRIZZLE,
    (CloudCoverBand.MOSTLY, HumidityBand.MILD): PrecipitationIntensityBand.LIGHT,
    (CloudCoverBand.MOSTLY, HumidityBand.HUMID): PrecipitationIntensityBand.STEADY,
    (CloudCoverBand.MOSTLY, HumidityBand.MUGGY): PrecipitationIntensityBand.STEADY,
    (CloudCoverBand.MOSTLY, HumidityBand.SOAKING): PrecipitationIntensityBand.HEAVY,
    # -- OVERCAST --
    (CloudCoverBand.OVERCAST, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.OVERCAST, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.OVERCAST, HumidityBand.CRISP): PrecipitationIntensityBand.DRIZZLE,
    (CloudCoverBand.OVERCAST, HumidityBand.MILD): PrecipitationIntensityBand.LIGHT,
    (CloudCoverBand.OVERCAST, HumidityBand.HUMID): PrecipitationIntensityBand.HEAVY,
    (CloudCoverBand.OVERCAST, HumidityBand.MUGGY): PrecipitationIntensityBand.HEAVY,
    (CloudCoverBand.OVERCAST, HumidityBand.SOAKING): PrecipitationIntensityBand.TORRENTIAL,
    # -- LEADEN --
    (CloudCoverBand.LEADEN, HumidityBand.ARID): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.LEADEN, HumidityBand.DRY): PrecipitationIntensityBand.NONE,
    (CloudCoverBand.LEADEN, HumidityBand.CRISP): PrecipitationIntensityBand.DRIZZLE,
    (CloudCoverBand.LEADEN, HumidityBand.MILD): PrecipitationIntensityBand.STEADY,
    (CloudCoverBand.LEADEN, HumidityBand.HUMID): PrecipitationIntensityBand.HEAVY,
    (CloudCoverBand.LEADEN, HumidityBand.MUGGY): PrecipitationIntensityBand.TORRENTIAL,
    (CloudCoverBand.LEADEN, HumidityBand.SOAKING): PrecipitationIntensityBand.CLOUDBURST,
}
