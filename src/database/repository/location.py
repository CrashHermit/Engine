from arcadedb_embedded.graph import Edge, Vertex

from core.model.database import EdgeType, VertexType
from database.repository.base import BaseRepository


class LocationRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base

    def get_location(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.LOCATION, id=id)

    def create_location(self, name: str, description: str) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.LOCATION,
            name=name,
            description=description,
        )

    def connect_location(self, from_location: Vertex, to_location: Vertex) -> Edge:
        return self._base.create_edge(
            type_name=EdgeType.CONNECTS,
            source=from_location,
            target=to_location,
        )

    def get_neighbors(self, location: Vertex) -> list[Vertex]:
        out_neighbors = [edge.get_target() for edge in location.get_out_edges(EdgeType.CONNECTS)]
        in_neighbors = [edge.get_source() for edge in location.get_in_edges(EdgeType.CONNECTS)]
        return list(set(out_neighbors + in_neighbors))
