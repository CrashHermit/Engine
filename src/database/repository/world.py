from typing import Any

from arcadedb_embedded.graph import Vertex

from src.database.repository.base import BaseRepository
from src.core.model.database import VertexType

VERTEX_NAME = "WORLD"


class WorldRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_world_vertex(self, **properties: Any) -> Vertex:
        world_vertex: Vertex = self._base.create_vertex(
            type_name=VertexType.WORLD, id=VERTEX_NAME, **properties
        )
        return world_vertex

    def get_world_vertex(self) -> Vertex | None:
        world_vertex: Vertex | None = self._base.get_vertex(
            type_name=VertexType.WORLD, id=VERTEX_NAME
        )
        return world_vertex

    def update_world_vertex(self, **properties: Any) -> Vertex:
        world_vertex: Vertex | None = self._base.get_vertex(
            type_name=VertexType.WORLD, id=VERTEX_NAME
        )
        updated_world_vertex: Vertex = self._base.update_vertex(
            vertex=world_vertex, **properties
        )
        return updated_world_vertex

    def delete_world_vertex(self) -> None:
        world_vertex: Vertex | None = self._base.get_vertex(
            type_name=VertexType.WORLD, id=VERTEX_NAME
        )
        self._base.delete_vertex(vertex=world_vertex)
