from enum import StrEnum


class TemperatureBand(StrEnum):
    FRIGID = "frigid"
    FREEZING = "freezing"
    COOL = "cool"
    MILD = "mild"
    WARM = "warm"
    HOT = "hot"
    SCORCHING = "scorching"


ORDER: tuple[TemperatureBand, ...] = (
    TemperatureBand.FRIGID,
    TemperatureBand.FREEZING,
    TemperatureBand.COOL,
    TemperatureBand.MILD,
    TemperatureBand.WARM,
    TemperatureBand.HOT,
    TemperatureBand.SCORCHING,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
