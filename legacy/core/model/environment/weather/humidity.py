from enum import StrEnum


class HumidityBand(StrEnum):
    ARID = "arid"
    DRY = "dry"
    CRISP = "crisp"
    MILD = "mild"
    HUMID = "humid"
    MUGGY = "muggy"
    SOAKING = "soaking"


ORDER: tuple[HumidityBand, ...] = (
    HumidityBand.ARID,
    HumidityBand.DRY,
    HumidityBand.CRISP,
    HumidityBand.MILD,
    HumidityBand.HUMID,
    HumidityBand.MUGGY,
    HumidityBand.SOAKING,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
