from arcadedb_embedded.graph import Vertex

from src.database.repository.base import BaseRepository
from src.core.model.database import VertexType


class WorldRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_world_vertex(self, name: str) -> Vertex:
        return self._base.create_vertex(type_name=VertexType.WORLD, name=name)

    def update_world_vertex(self, world_vertex: Vertex, name: str) -> Vertex:
        return self._base.update_vertex(vertex=world_vertex, name=name)

    def get_world_vertex(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.WORLD, id=id)
