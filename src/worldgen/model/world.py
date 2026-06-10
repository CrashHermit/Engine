from __future__ import annotations

from dataclasses import dataclass, field

from src.worldgen.model.topology import GridTile, RiverSegment, VoronoiMesh


@dataclass
class WorldSpec:
    """Immutable input to the worldgen pipeline.

    Holds only the knobs a caller supplies; everything else is generated.
    """

    size: int = 100
    seed: int = 0
    name: str = ""


@dataclass
class WorldData:
    """The generated world artifact produced by the pipeline.

    Accumulated in place during a run (the working state) and returned as the
    final output. ``mesh`` is non-optional and starts empty, so stages never
    need to guard against a missing mesh.
    """

    mesh: VoronoiMesh = field(default_factory=lambda: VoronoiMesh(0.0, 0.0))
    grid: list[GridTile] = field(default_factory=list)
    rivers: list[RiverSegment] = field(default_factory=list)
    landmass_sizes: dict[int, int] = field(default_factory=dict)
