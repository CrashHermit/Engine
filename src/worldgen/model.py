"""Results produced by the current world-generation pipeline."""

from dataclasses import dataclass

from src.worldgen.geometry.mesh import Mesh
from src.worldgen.geology.model import GeologyResult


@dataclass(frozen=True, slots=True)
class GeneratedWorld:
    mesh: Mesh
    geology: GeologyResult
