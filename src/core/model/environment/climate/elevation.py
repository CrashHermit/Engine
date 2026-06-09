from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ElevationEnum(IntEnum):
    SUNKEN = 0
    LOWLAND = 1
    ROLLING = 2
    MIDLAND = 3
    HIGHLAND = 4
    LOFTY = 5
    SUMMIT = 6


@dataclass
class ElevationData:
    elevation: ElevationEnum
