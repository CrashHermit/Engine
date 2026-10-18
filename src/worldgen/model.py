"""Results produced by the world-generation pipeline."""

from dataclasses import dataclass

from src.worldgen.elevation.model import ElevationResult
from src.worldgen.elevation.field import ElevationField
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.model import GeologyResult
from src.worldgen.surface.field import SurfaceField
from src.worldgen.surface.model import SurfaceResult


@dataclass(frozen=True, slots=True)
class GeneratedWorld:
    mesh: Mesh
    geology: GeologyResult
    elevation: ElevationResult
    surface: SurfaceResult
    radius_m: float
    elevation_field: ElevationField
    surface_field: SurfaceField
