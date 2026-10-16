"""Coastal and tectonic elevation generation."""

from src.worldgen.elevation.config import (
    BuoyancyConfig,
    CoastalWidthConfig,
    CollisionConfig,
    DeformationConfig,
    DivergenceConfig,
    ElevationConfig,
    SubductionConfig,
    TransformConfig,
)
from src.worldgen.elevation.generate import generate_elevation
from src.worldgen.elevation.model import ElevationResult

__all__ = [
    "BuoyancyConfig",
    "CoastalWidthConfig",
    "CollisionConfig",
    "DeformationConfig",
    "DivergenceConfig",
    "ElevationConfig",
    "ElevationResult",
    "SubductionConfig",
    "TransformConfig",
    "generate_elevation",
]
