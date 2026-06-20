from src.core.model.environment.climate.precipitation import PrecipitationBand
from src.core.model.environment.ecology.biome import BIOME_GRID, BiomeEnum
from src.core.model.environment.shared.temperature import TemperatureBand


class Biome:
    def biome_from_climate(
        self,
        temperature: TemperatureBand,
        precipitation: PrecipitationBand,
    ) -> BiomeEnum:
        return BIOME_GRID[(temperature, precipitation)]
