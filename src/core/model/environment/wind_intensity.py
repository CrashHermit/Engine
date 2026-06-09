from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class WindIntensityEnum(IntEnum):
    CALM = 0
    GENTLE = 1
    BREEZY = 2
    BLUSTERY = 3
    GALE = 4
    STORM = 5
    HURRICANE = 6


@dataclass
class WindIntensityData:
    wind_intensity: WindIntensityEnum
