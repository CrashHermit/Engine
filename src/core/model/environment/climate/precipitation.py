from dataclasses import dataclass
from enum import IntEnum


class PrecipitationEnum(IntEnum):
    HYPER_ARID = 0
    ARID = 1
    SEMI_ARID = 2
    SUB_HUMID = 3
    HUMID = 4
    HYPER_HUMID = 5
    SATURATED = 6


@dataclass
class PrecipitationData:
    precipitation: PrecipitationEnum
