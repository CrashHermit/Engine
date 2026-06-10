from __future__ import annotations

from src.core.model.environment.ecology.alignment import (
    BREAKPOINTS,
    ORDER,
    AlignmentBand,
)


class Alignment:
    def alignment_band(self, value: float) -> AlignmentBand:
        # Worldgen emits alignment on a signed [-1, 1] axis (-1 = evil,
        # 0 = neutral, +1 = good); remap to [0, 1] so the equal-thirds
        # BREAKPOINTS split it symmetrically (0 -> 0.5 -> NEUTRAL).
        normalized: float = (max(-1.0, min(1.0, value)) + 1.0) * 0.5
        for index, edge in enumerate(BREAKPOINTS):
            if normalized < edge:
                return ORDER[index]
        return ORDER[-1]

    def alignment_index(self, band: AlignmentBand) -> int:
        return ORDER.index(band)
