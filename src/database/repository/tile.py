from __future__ import annotations

from arcadedb_embedded.graph import Edge, Vertex

from core.model.environment.climate.biome import BiomeEnum
from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository
from worldgen.data import GridPositionData
from worldgen.stages import landmass


class TileRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def get_tile(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.TILE, id=id)

    def create_tile(
        self, 
        x: int, 
        y: int, 
        z: int, 
        is_land: bool, 
        landmass_id: int,
        temperature: float,
        precipitation: float,
        wind_u: float,
        wind_v: float,
        wind_magnitude: float,
        biomes: list[BiomeEnum]
    ) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.TILE, 
            x=x, 
            y=y,
            z=z,
            is_land=is_land,
            landmass_id=landmass_id,
            temperature=temperature,
            precipitation=precipitation,
            wind_u=wind_u,
            wind_v=wind_v,
            wind_magnitude=wind_magnitude,
            biomes=biomes
        )        

    def connect_tiles(self, a: Vertex, b: Vertex) -> Edge:
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