from enum import StrEnum


class WindIntensityBand(StrEnum):
    CALM = "calm"
    GENTLE = "gentle"
    BREEZY = "breezy"
    BLUSTERY = "blustery"
    GALE = "gale"
    STORM = "storm"
    HURRICANE = "hurricane"


ORDER: tuple[WindIntensityBand, ...] = (
    WindIntensityBand.CALM,
    WindIntensityBand.GENTLE,
    WindIntensityBand.BREEZY,
    WindIntensityBand.BLUSTERY,
    WindIntensityBand.GALE,
    WindIntensityBand.STORM,
    WindIntensityBand.HURRICANE,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
