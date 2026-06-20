from src.core.model.environment.ecology.biome import BiomeEnum
from src.core.model.environment.shared.wind_intensity import WindIntensityBand
from src.core.model.environment.weather.particulate_type import (
    PARTICULATE_TYPE_GRID,
    ParticulateTypeEnum,
)


class ParticulateType:
    def particulatetype_from_environment(
        self,
        biome: BiomeEnum,
        wind_intensity: WindIntensityBand,
    ) -> ParticulateTypeEnum:
        return PARTICULATE_TYPE_GRID.get(
            (biome, wind_intensity), ParticulateTypeEnum.NONE
        )
