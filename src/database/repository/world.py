from __future__ import annotations

from arcadedb_embedded.graph import Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


class WorldRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    # PROTOTYPE START
    def get_start_location(self) -> Vertex | None:
        worlds = self._base.list_vertices(VertexType.WORLD)
        if not worlds:
            return None
        edges = worlds[0].get_out_edges(EdgeType.HAS_START)
        return edges[0].get_in() if edges else None

    # PROTOTYPE END

    def create_world(
        self,
        name: str,
        description: str,
        size: int,
    ) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.WORLD,
            name=name,
            description=description,
            size=size,
            elapsed_ticks=0,
        )

    # ── World clock (decision: the tick count is a scalar on the singleton
    # WORLD vertex, owned here; behaviour lives in TimeService) ──────────────
    def _world(self) -> Vertex | None:
        worlds = self._base.list_vertices(VertexType.WORLD)
        return worlds[0] if worlds else None

    def get_elapsed_ticks(self) -> int:
        world = self._world()
        if world is None:
            return 0
        return int(world.get(name="elapsed_ticks") or 0)

    def advance_elapsed_ticks(self, delta: int) -> int:
        """Add `delta` ticks to the world clock and return the new total.

        A non-positive delta is a no-op (the clock is monotonic).
        """
        world = self._world()
        if world is None:
            return 0
        current = int(world.get(name="elapsed_ticks") or 0)
        if delta <= 0:
            return current
        new_total = current + delta
        self._base.update_vertex(world, elapsed_ticks=new_total)
        return new_total
