from src.core.model.environment.weather.cloud_cover import (
    BREAKPOINTS,
    ORDER,
    CloudCoverBand,
)


class CloudCover:
    def cloudcover_band(self, value: float) -> CloudCoverBand:
        clamped: float = max(0.0, min(1.0, value))
        for index, edge in enumerate(BREAKPOINTS):
            if clamped < edge:
                return ORDER[index]
        return ORDER[-1]

    def cloudcover_index(self, band: CloudCoverBand) -> int:
        return ORDER.index(band)
