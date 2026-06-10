from __future__ import annotations

from dataclasses import dataclass, field

from src.worldgen.model.environment import CellEnvironment


@dataclass
class MeshCell:
    """A single Voronoi cell: geometry plus its shared attribute bundle."""

    id: int
    site: tuple[float, float]
    neighbors: list[int] = field(default_factory=list)
    env: CellEnvironment = field(default_factory=CellEnvironment)


@dataclass
class VoronoiMesh:
    """The periodic Voronoi mesh every simulation layer runs on."""

    width: float
    height: float
    cells: list[MeshCell] = field(default_factory=list)


@dataclass
class GridTile:
    """A single gameplay grid tile: coordinates plus the shared bundle."""

    x: int
    y: int
    env: CellEnvironment = field(default_factory=CellEnvironment)


@dataclass
class LakeBasin:
    tiles: set[tuple[int, int]]
    spillway: tuple[int, int] | None


@dataclass
class RiverSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    flux: float
