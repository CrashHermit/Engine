from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


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

    def create_test_location(self) -> None:
        locations = []
        for i in range(7):
            location = self.create_location(
                name=f"Test Location {i}",
                description=f"This is a test location {i}",
            )
            locations.append(location)

        for i in range(6):
            self.connect_location(
                from_location=locations[0],
                to_location=locations[i + 1],
            )
        self.connect_location(
            from_location=locations[1],
            to_location=locations[2],
        )
        self.connect_location(
            from_location=locations[2],
            to_location=locations[3],
        )
        self.connect_location(
            from_location=locations[3],
            to_location=locations[4],
        )
        self.connect_location(
            from_location=locations[4],
            to_location=locations[5],
        )
        self.connect_location(
            from_location=locations[5],
            to_location=locations[6],
        )
        self.connect_location(
            from_location=locations[6],
            to_location=locations[1],
        )

