from database.repository.base import BaseRepository
from arcadedb_embedded.graph import Edge, Vertex
from core.model.database import EdgeType, VertexType


class LocationRepository(BaseRepository):

    def get_location(self, id: str) -> Vertex | None:
        return self.get_vertex(type_name=VertexType.LOCATION, id=id)

    def create_location(self, name: str, description: str) -> Vertex:
        return self.create_vertex(
            type_name=VertexType.LOCATION,
            name=name,
            description=description,
        )

    def connect_location(self, from_location: Vertex, to_location: Vertex) -> Edge:
        return self.create_edge(
            type_name=EdgeType.CONNECTS,
            source=from_location,
            target=to_location,
        )

    def get_neighbors(self, location: Vertex) -> list[Vertex]:
        all_edges: list[Edge] = location.get_out_edges(EdgeType.CONNECTS) + location.get_in_edges(EdgeType.CONNECTS)
        return list[Vertex](set[Vertex]([edge.get_target() for edge in all_edges]))
