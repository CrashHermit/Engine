from src.core.model.environment.ecology.alignment import (
    BREAKPOINTS,
    ORDER,
    AlignmentBand,
)


class Alignment:
    def alignment_band(self, value: float) -> AlignmentBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def alignment_index(self, band: AlignmentBand) -> int:
        return ORDER.index(band)
