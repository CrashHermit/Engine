from arcadedb_embedded.graph import Edge, Vertex
from src.core.model.entity import Danger
from src.core.model.threat import Channel
from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository
from src.core.model.location import EntityData


class LocationRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base

    def get_location(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.LOCATION, id=id)

    def create_location(self, name: str, description: str, is_center: bool = False) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.LOCATION,
            name=name,
            description=description,
            is_center=is_center,
        )

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

    def create_entity(
        self,
        location: Vertex,
        name: str,
        description: str,
        scene_position: str,
        danger: str = "standard",
        threat_channels: str = "",
    ) -> Vertex:
        entity = self._base.create_vertex(
            type_name=VertexType.ENTITY,
            name=name,
            description=description,
            scene_position=scene_position,
            danger=danger,
            threat_channels=threat_channels,
        )
        self._base.create_edge(type_name=EdgeType.CONTAINS, source=location, target=entity)
        return entity

    def get_entities(self, location: Vertex) -> list[Vertex]:
        return [edge.get_in() for edge in location.get_out_edges(EdgeType.CONTAINS)]

    def _to_entity_data(self, entity: Vertex) -> EntityData:
        channels_csv = entity.get(name="threat_channels") or ""
        channels = frozenset(
            Channel(c) for c in (s.strip() for s in channels_csv.split(",")) if c
        )
        danger_raw = entity.get(name="danger") or Danger.STANDARD.value
        return EntityData(
            id=entity.get(name="id") or "",
            name=entity.get(name="name") or "",
            description=entity.get(name="description") or "",
            scene_position=entity.get(name="scene_position") or "",
            danger=Danger(danger_raw),
            threat_channels=channels,
        )