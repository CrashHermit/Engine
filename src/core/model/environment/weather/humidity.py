from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class HumidityEnum(IntEnum):
    ARID = 0
    DRY = 1
    CRISP = 2
    MILD = 3
    HUMID = 4
    MUGGY = 5
    SOAKING = 6


@dataclass
class HumidityData:
    humidity: HumidityEnum
