"""Configuration for composing relief processes."""

from dataclasses import dataclass, field

from src.worldgen.relief.coastal import SourceCoastalConfig
from src.worldgen.relief.impact import ImpactConfig
from src.worldgen.relief.ridge_detail import RidgeDetailConfig
from src.worldgen.relief.tectonic_response import TectonicResponseConfig
from src.worldgen.relief.variation import TerrainVariationConfig
from src.worldgen.relief.volcanism import VolcanismConfig


@dataclass(frozen=True, slots=True)
class ReliefConfig:
    """Source relief profiles and independent world-space impacts and variation."""

    coastal: SourceCoastalConfig = field(default_factory=SourceCoastalConfig)
    tectonic: TectonicResponseConfig = field(default_factory=TectonicResponseConfig)
    variation: TerrainVariationConfig = field(default_factory=TerrainVariationConfig)
    ridge_detail: RidgeDetailConfig = field(default_factory=RidgeDetailConfig)
    volcanism: VolcanismConfig = field(default_factory=VolcanismConfig)
    impacts: ImpactConfig = field(default_factory=ImpactConfig)
