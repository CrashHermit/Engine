from dataclasses import dataclass
from enum import IntEnum


class TemperatureEnum(IntEnum):
    FRIGID = 0
    FREEZING = 1
    COOL = 2
    MILD = 3
    WARM = 4
    HOT = 5
    SCORCHING = 6


@dataclass
class TemperatureData:
    temperature: TemperatureEnum
