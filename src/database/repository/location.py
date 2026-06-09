from __future__ import annotations

from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository
from worldgen.data import GridPositionData


class LocationRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def get_location(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.LOCATION, id=id)

    def create_location(self, x: int, y: int) -> Vertex:
        return self._base.create_vertex(type_name=VertexType.LOCATION, x=x, y=y)

    def update_location_climate(self, id: str, grid_position_data: GridPositionData) -> None:
        

    def connect_locations(self, a: Vertex, b: Vertex) -> Edge:
        return self._base.create_edge(
            type_name=EdgeType.CONNECTS,
            source=a,
            target=b,
        )

    def get_neighbors(self, location: Vertex) -> list[Vertex]:
        neighbors = []
        for edge in location.get_both_edges(EdgeType.CONNECTS):
            if edge.get_out().get_rid() == location.get_rid():
                neighbors.append(edge.get_in())
            else:
                neighbors.append(edge.get_out())
        return neighbors

    def get_entities(self, location: Vertex) -> list[Vertex]:
        return [edge.get_in() for edge in location.get_out_edges(EdgeType.CONTAINS)]

    def get_entity(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.ENTITY, id=id)

    def set_entity_resolution(self, entity: Vertex, resolution: str) -> None:
        self._base.update_vertex(entity, resolution=resolution)

    def remove_entity(self, entity: Vertex) -> None:
        self._base.delete_vertex(entity)
