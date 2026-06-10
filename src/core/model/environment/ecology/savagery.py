from __future__ import annotations

from enum import StrEnum


class SavageryBand(StrEnum):
    TAME = "tame"
    BENIGN = "benign"
    PLACID = "placid"
    WILD = "wild"
    RUGGED = "rugged"
    SAVAGE = "savage"
    PRIMAL = "primal"


ORDER: tuple[SavageryBand, ...] = (
    SavageryBand.TAME,
    SavageryBand.BENIGN,
    SavageryBand.PLACID,
    SavageryBand.WILD,
    SavageryBand.RUGGED,
    SavageryBand.SAVAGE,
    SavageryBand.PRIMAL,
)

BREAKPOINTS: tuple[float, ...] = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
