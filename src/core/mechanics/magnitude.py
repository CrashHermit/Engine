"""The single 1-4 magnitude ladder (decision #15).

Every consequence type and every harm level rides one ladder:
`0 none - 1 Minor - 2 Standard - 3 Severe - 4 Fatal`. Code owns the numbers;
the narrator owns the fiction.
"""

from __future__ import annotations

from enum import IntEnum

MIN_MAGNITUDE = 0
MAX_MAGNITUDE = 4


class Magnitude(IntEnum):
    NONE = 0
    MINOR = 1
    STANDARD = 2
    SEVERE = 3
    FATAL = 4


def clamp_magnitude(value: int) -> int:
    """Pin a magnitude into the valid `0..4` band."""
    return max(MIN_MAGNITUDE, min(MAX_MAGNITUDE, value))
