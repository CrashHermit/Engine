from enum import IntEnum

MIN_MAGNITUDE: int = 0
MAX_MAGNITUDE: int = 4


class Magnitude(IntEnum):
    NONE = 0
    MINOR = 1
    STANDARD = 2
    SEVERE = 3
    FATAL = 4


def clamp_magnitude(magnitude: int) -> int:
    return max(MIN_MAGNITUDE, min(magnitude, MAX_MAGNITUDE))
