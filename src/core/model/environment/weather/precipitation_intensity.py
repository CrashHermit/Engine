from dataclasses import dataclass
from enum import IntEnum

from src.core.model.environment.weather.cloud_cover import CloudCoverEnum
from src.core.model.environment.weather.humidity import HumidityEnum


class PrecipitationIntensityEnum(IntEnum):
    NONE = 0
    DRIZZLE = 1
    LIGHT = 2
    STEADY = 3
    HEAVY = 4
    TORRENTIAL = 5
    CLOUDBURST = 6


@dataclass
class PrecipitationIntensityData:
    precipitation_intensity: PrecipitationIntensityEnum


class PrecipitationIntensity:
    """Map cloud cover and humidity to a precipitation intensity."""

    precipitation_intensity_grid: dict[
        tuple[CloudCoverEnum, HumidityEnum], PrecipitationIntensityEnum
    ] = {
        # ── CLEAR ─────────────────────────────────────────────────────────────
        (CloudCoverEnum.CLEAR, HumidityEnum.ARID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.CLEAR, HumidityEnum.DRY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.CLEAR, HumidityEnum.CRISP): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.CLEAR, HumidityEnum.MILD): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.CLEAR, HumidityEnum.HUMID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.CLEAR, HumidityEnum.MUGGY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.CLEAR, HumidityEnum.SOAKING): PrecipitationIntensityEnum.NONE,
        # ── FEW ─────────────────────────────────────────────────────────────────
        (CloudCoverEnum.FEW, HumidityEnum.ARID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.FEW, HumidityEnum.DRY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.FEW, HumidityEnum.CRISP): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.FEW, HumidityEnum.MILD): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.FEW, HumidityEnum.HUMID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.FEW, HumidityEnum.MUGGY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.FEW, HumidityEnum.SOAKING): PrecipitationIntensityEnum.NONE,
        # ── SCATTERED ───────────────────────────────────────────────────────────
        (CloudCoverEnum.SCATTERED, HumidityEnum.ARID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.SCATTERED, HumidityEnum.DRY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.SCATTERED, HumidityEnum.CRISP): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.SCATTERED, HumidityEnum.MILD): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.SCATTERED, HumidityEnum.HUMID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.SCATTERED, HumidityEnum.MUGGY): PrecipitationIntensityEnum.DRIZZLE,
        (CloudCoverEnum.SCATTERED, HumidityEnum.SOAKING): PrecipitationIntensityEnum.LIGHT,
        # ── BROKEN ──────────────────────────────────────────────────────────────
        (CloudCoverEnum.BROKEN, HumidityEnum.ARID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.BROKEN, HumidityEnum.DRY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.BROKEN, HumidityEnum.CRISP): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.BROKEN, HumidityEnum.MILD): PrecipitationIntensityEnum.DRIZZLE,
        (CloudCoverEnum.BROKEN, HumidityEnum.HUMID): PrecipitationIntensityEnum.LIGHT,
        (CloudCoverEnum.BROKEN, HumidityEnum.MUGGY): PrecipitationIntensityEnum.LIGHT,
        (CloudCoverEnum.BROKEN, HumidityEnum.SOAKING): PrecipitationIntensityEnum.STEADY,
        # ── MOSTLY ──────────────────────────────────────────────────────────────
        (CloudCoverEnum.MOSTLY, HumidityEnum.ARID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.MOSTLY, HumidityEnum.DRY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.MOSTLY, HumidityEnum.CRISP): PrecipitationIntensityEnum.DRIZZLE,
        (CloudCoverEnum.MOSTLY, HumidityEnum.MILD): PrecipitationIntensityEnum.LIGHT,
        (CloudCoverEnum.MOSTLY, HumidityEnum.HUMID): PrecipitationIntensityEnum.STEADY,
        (CloudCoverEnum.MOSTLY, HumidityEnum.MUGGY): PrecipitationIntensityEnum.STEADY,
        (CloudCoverEnum.MOSTLY, HumidityEnum.SOAKING): PrecipitationIntensityEnum.HEAVY,
        # ── OVERCAST ────────────────────────────────────────────────────────────
        (CloudCoverEnum.OVERCAST, HumidityEnum.ARID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.OVERCAST, HumidityEnum.DRY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.OVERCAST, HumidityEnum.CRISP): PrecipitationIntensityEnum.DRIZZLE,
        (CloudCoverEnum.OVERCAST, HumidityEnum.MILD): PrecipitationIntensityEnum.LIGHT,
        (CloudCoverEnum.OVERCAST, HumidityEnum.HUMID): PrecipitationIntensityEnum.HEAVY,
        (CloudCoverEnum.OVERCAST, HumidityEnum.MUGGY): PrecipitationIntensityEnum.HEAVY,
        (CloudCoverEnum.OVERCAST, HumidityEnum.SOAKING): PrecipitationIntensityEnum.TORRENTIAL,
        # ── LEADEN ──────────────────────────────────────────────────────────────
        (CloudCoverEnum.LEADEN, HumidityEnum.ARID): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.LEADEN, HumidityEnum.DRY): PrecipitationIntensityEnum.NONE,
        (CloudCoverEnum.LEADEN, HumidityEnum.CRISP): PrecipitationIntensityEnum.DRIZZLE,
        (CloudCoverEnum.LEADEN, HumidityEnum.MILD): PrecipitationIntensityEnum.STEADY,
        (CloudCoverEnum.LEADEN, HumidityEnum.HUMID): PrecipitationIntensityEnum.HEAVY,
        (CloudCoverEnum.LEADEN, HumidityEnum.MUGGY): PrecipitationIntensityEnum.TORRENTIAL,
        (CloudCoverEnum.LEADEN, HumidityEnum.SOAKING): PrecipitationIntensityEnum.CLOUDBURST,
    }

    def get_precipitation_intensity(
        self,
        cloud_cover_enum: CloudCoverEnum,
        humidity_enum: HumidityEnum,
    ) -> PrecipitationIntensityEnum:
        """Look up the precipitation intensity for a cloud cover and humidity pair."""
        return self.precipitation_intensity_grid.get(
            (cloud_cover_enum, humidity_enum), PrecipitationIntensityEnum.NONE
        )
