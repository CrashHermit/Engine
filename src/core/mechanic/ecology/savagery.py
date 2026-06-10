from __future__ import annotations

from src.core.model.environment.ecology.savagery import (
    BREAKPOINTS,
    ORDER,
    SavageryBand,
)


class Savagery:
    def savagery_band(self, value: float) -> SavageryBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def savagery_index(self, band: SavageryBand) -> int:
        return ORDER.index(band)
