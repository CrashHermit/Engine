from typing import Any

from arcadedb_embedded.graph import Vertex

from src.core.model.database import VertexType
from src.database.repository.base import BaseRepository

VERTEX_NAME = "TIME"


class TimeRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_time_vertex(self, **properties: Any) -> Vertex:
        time_vertex: Vertex = self._base.create_vertex(
            type_name=VertexType.TIME, id=VERTEX_NAME, **properties
        )
        return time_vertex

    def get_time_vertex(self) -> Vertex | None:
        time_vertex: Vertex | None = self._base.get_vertex(
            type_name=VertexType.TIME, id=VERTEX_NAME
        )
        return time_vertex

    def update_time_vertex(self, **properties: Any) -> Vertex:
        time_vertex: Vertex | None = self._base.get_vertex(
            type_name=VertexType.TIME, id=VERTEX_NAME
        )
        updated_time_vertex: Vertex = self._base.update_vertex(
            vertex=time_vertex, **properties
        )
        return updated_time_vertex

    def delete_time_vertex(self) -> None:
        time_vertex: Vertex | None = self._base.get_vertex(
            type_name=VertexType.TIME, id=VERTEX_NAME
        )
        self._base.delete_vertex(vertex=time_vertex)
