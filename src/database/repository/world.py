from __future__ import annotations

from arcadedb_embedded.graph import Edge, Vertex

from src.database.repository.base import BaseRepository
from src.core.model.database import EdgeType, VertexType

class WorldRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_world_vertex(self) -> Vertex:
        return self._base.create_vertex(type_name=VertexType.WORLD)

    def get_world_vertex(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.WORLD, id=id)