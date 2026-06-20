from dataclasses import dataclass


@dataclass(frozen=True)
class WorldDateTime:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
