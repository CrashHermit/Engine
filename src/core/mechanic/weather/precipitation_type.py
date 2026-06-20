from src.core.model.environment.shared.temperature import TemperatureBand
from src.core.model.environment.weather.precipitation_intensity import (
    PrecipitationIntensityBand,
)
from src.core.model.environment.weather.precipitation_type import (
    PRECIPITATION_TYPE_GRID,
    PrecipitationTypeEnum,
)


class PrecipitationType:
    def precipitationtype_from_weather(
        self,
        temperature: TemperatureBand,
        intensity: PrecipitationIntensityBand,
    ) -> PrecipitationTypeEnum:
        return PRECIPITATION_TYPE_GRID.get(
            (temperature, intensity), PrecipitationTypeEnum.NONE
        )
