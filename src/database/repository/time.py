from __future__ import annotations

from arcadedb_embedded.graph import Vertex

from core.model.database import VertexType
from src.database.repository.base import BaseRepository


class TimeRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base
        self._time_vertex: Vertex | None = self._base.get_vertex(type_name=VertexType.TIME)
        self._current_ticks

    def get_elapsed_ticks(self) -> int:
        return int(self._time_vertex.get(name="elapsed_ticks") or 0)

    def advance_elapsed_ticks(self, delta: int) -> int:
        current = self.get_elapsed_ticks()
        return new_total