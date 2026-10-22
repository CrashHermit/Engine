"""Sampled world artifact produced by the continuous field engine."""

from dataclasses import dataclass

from src.worldgen.elevation.model import ElevationResult
from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.model import GeologyResult
from src.worldgen.surface.field import SurfaceField
from src.worldgen.surface.model import SurfaceResult
from src.worldgen.world import WorldField


@dataclass(frozen=True, slots=True)
class GeneratedWorld:
    mesh: Mesh
    geology: GeologyResult
    elevation: ElevationResult
    surface: SurfaceResult
    radius_m: float
    field: WorldField
    surface_field: SurfaceField
