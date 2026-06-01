from src.database.repository.base import BaseRepository
from arcadedb_embedded.graph import Vertex
from src.core.model.database import VertexType

class EntityRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_entity(self, name: str, description: str) -> Vertex:
        return self._base.create_vertex(type_name=VertexType.NPC, name=name, description=description)

    def update_entity(self, entity: Vertex, name: str, description: str) -> None:
        pass

    def delete_entity(self, entity: Vertex) -> None:
        pass

    def get_entity(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.NPC, id=id)

    def list_entities(self) -> list[Vertex]:
        return self._base.list_vertices(type_name=VertexType.ENTITY)

    def place_entity(self, entity: Vertex, location: Vertex) -> None:
        pass

    def move_entity(self, entity: Vertex, to_location: Vertex) -> None:
        pass

    def get_current_location(self, entity: Vertex) -> Vertex | None:
        pass

