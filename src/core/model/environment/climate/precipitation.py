from __future__ import annotations

from enum import StrEnum


class PrecipitationBand(StrEnum):
    HYPER_ARID = "hyper_arid"
    ARID = "arid"
    SEMI_ARID = "semi_arid"
    SUB_HUMID = "sub_humid"
    HUMID = "humid"
    HYPER_HUMID = "hyper_humid"
    SATURATED = "saturated"


ORDER: tuple[PrecipitationBand, ...] = (
    PrecipitationBand.HYPER_ARID,
    PrecipitationBand.ARID,
    PrecipitationBand.SEMI_ARID,
    PrecipitationBand.SUB_HUMID,
    PrecipitationBand.HUMID,
    PrecipitationBand.HYPER_HUMID,
    PrecipitationBand.SATURATED,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
