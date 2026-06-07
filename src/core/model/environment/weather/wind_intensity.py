from enum import IntEnum
from dataclasses import dataclass


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