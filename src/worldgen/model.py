"""Results produced by the world-generation pipeline."""

from dataclasses import dataclass

from src.worldgen.geometry.mesh import Mesh

from src.worldgen.geology.model import GeologyResult
from src.worldgen.terrain.model import TerrainResult


@dataclass(frozen=True, slots=True)
class GeneratedWorld:
    mesh: Mesh
    geology: GeologyResult
    terrain: TerrainResult
