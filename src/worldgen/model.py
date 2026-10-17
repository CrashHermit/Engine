"""Results produced by the world-generation pipeline."""

from dataclasses import dataclass

from src.worldgen.elevation.model import ElevationResult
from src.worldgen.elevation.field import ElevationField
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.model import GeologyResult


@dataclass(frozen=True, slots=True)
class GeneratedWorld:
    mesh: Mesh
    geology: GeologyResult
    elevation: ElevationResult
    radius_m: float
    elevation_field: ElevationField
