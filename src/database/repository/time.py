from __future__ import annotations

from arcadedb_embedded.graph import Vertex

from src.core.model.database import VertexType
from src.database.repository.base import BaseRepository


class TimeRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def get_time_vertex(self) -> Vertex | None:
        time_vertex: Vertex | None = self._base.get_vertex(type_name=VertexType.TIME)
        return time_vertex

    def advance_elapsed_ticks(self, delta: int) -> Vertex:
        time_vertex: Vertex | None = self.get_time_vertex()
        current_ticks = time_vertex.get(name="elapsed_ticks")
        advanced_ticks = current_ticks + delta
        time_vertex.set(name="elapsed_ticks", value=advanced_ticks)
        self._base.update_vertex(time_vertex)

        return time_vertex

    