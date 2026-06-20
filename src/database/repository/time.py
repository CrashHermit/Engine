from arcadedb_embedded.graph import Vertex

from src.core.model.database import VertexType
from src.database.repository.base import BaseRepository


class TimeRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_time_vertex(self, elapsed_ticks: int) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.TIME,
            elapsed_ticks=elapsed_ticks,
        )

    def get_time_vertex(self) -> Vertex | None:
        time_vertex: Vertex | None = self._base.get_vertex(type_name=VertexType.TIME)
        return time_vertex

    def delete_time_vertex(self) -> None:
        time_vertex: Vertex | None = self.get_time_vertex()
        if time_vertex is None:
            return
        self._base.delete_vertex(vertex=time_vertex)

    def update_elapsed_ticks(self, elapsed_ticks: int) -> Vertex:
        time_vertex: Vertex | None = self.get_time_vertex()
        if time_vertex is None:
            return None
        current_elapsed_ticks: int = time_vertex.get(name="elapsed_ticks")
        new_elapsed_ticks: int = current_elapsed_ticks + elapsed_ticks
        return self._base.update_vertex(
            vertex=time_vertex, elapsed_ticks=new_elapsed_ticks
        )
