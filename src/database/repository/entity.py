from arcadedb_embedded.graph import Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


class EntityRepository:
    """Provide vertex-native entity persistence, decoupled from location.

    Placement is a CONTAINS edge (location → entity); the future spawner
    reuses this seam.
    """

    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def get_entity(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.ENTITY, id=id)

    def list_entities(self) -> list[Vertex]:
        return self._base.list_vertices(type_name=VertexType.ENTITY)

    def place_entity(self, entity: Vertex, location: Vertex) -> None:
        self._base.create_edge(
            type_name=EdgeType.CONTAINS, source=location, target=entity
        )

    def move_entity(self, entity: Vertex, to_location: Vertex) -> None:
        for edge in entity.get_in_edges(EdgeType.CONTAINS):
            self._base.delete_edge(edge)
        self.place_entity(entity, to_location)

    def get_current_location(self, entity: Vertex) -> Vertex | None:
        edges = list(entity.get_in_edges(EdgeType.CONTAINS))
        return edges[0].get_out() if edges else None

    def list_entities_at(self, location: Vertex) -> list[Vertex]:
        return [edge.get_in() for edge in location.get_out_edges(EdgeType.CONTAINS)]
