"""Continuous source elevation and world-space terrain variation."""

from src.worldgen.elevation.config import (
    ElevationConfig,
    SourceCoastalConfig,
    SourceCoastalSpanConfig,
    SourceReliefConfig,
    TerrainVariationConfig,
    TectonicResponseConfig,
)
from src.worldgen.elevation.field import SourceElevationField
from src.worldgen.elevation.generate import generate_elevation_field
from src.worldgen.elevation.model import ElevationResult, SourceElevationSample
from src.worldgen.elevation.source_coastal import (
    SourceCoastalField,
    SourceCoastalSample,
)
from src.worldgen.elevation.variation import TerrainVariationField
from src.worldgen.elevation.volcanism import (
    VolcanicField,
    VolcanicSample,
    VolcanismConfig,
)

__all__ = [
    "ElevationConfig",
    "ElevationResult",
    "SourceCoastalConfig",
    "SourceCoastalField",
    "SourceCoastalSample",
    "SourceCoastalSpanConfig",
    "SourceElevationField",
    "SourceElevationSample",
    "SourceReliefConfig",
    "TerrainVariationConfig",
    "TerrainVariationField",
    "TectonicResponseConfig",
    "VolcanicField",
    "VolcanicSample",
    "VolcanismConfig",
    "generate_elevation_field",
]
