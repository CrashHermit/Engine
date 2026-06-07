from dataclasses import dataclass
from enum import IntEnum


class CloudCoverEnum(IntEnum):
    CLEAR = 0
    FEW = 1
    SCATTERED = 2
    BROKEN = 3
    MOSTLY = 4
    OVERCAST = 5
    LEADEN = 6

@dataclass
class CloudCoverData:
    cloud_cover: CloudCoverEnum