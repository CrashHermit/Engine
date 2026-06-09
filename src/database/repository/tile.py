from __future__ import annotations

from arcadedb_embedded.graph import Edge, Vertex

from core.model.environment.climate.biome import BiomeEnum
from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


class TileRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def get_tile_vertex(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.TILE, id=id)

    def update_tile_vertex(
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
        return self._base.update_vertex(
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

    def create_tile_vertex(
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

    def get_tile_vertex_at(self, x: int, y: int) -> Vertex | None:
        return self._base.lookup_vertex(type_name=VertexType.TILE, keys=["x", "y"], values=[x, y])

    def get_tile_vertex_neighbors(self, tile: Vertex, size: int) -> list[Vertex]:
        """Uses offsets to calculate the values of the closest 8 neighbors for the tile.
        """
        offsets: list[tuple[int, int]] = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),          (1,  0),
            (-1,  1), (0,  1), (1,  1),
        ]

        x: int = int(tile.get(name="x"))
        y: int = int(tile.get(name="y"))

        neighbors: list[Vertex | None] = []

        for dx, dy in offsets:
            nx: int = (x + dx) % size
            ny: int = (y + dy) % size

            neighbor: Vertex | None = self.get_tile_vertex_at(x=nx, y=ny)

            if neighbor is None:
                raise LookupError(f"Missing tile at ({nx}, {ny})")

            neighbors.append(neighbor)

        return neighbors

    def create_has_tile_edge(self, source: Vertex, target: Vertex) -> Edge:
        edge: Edge = self._base.create_edge(type_name=EdgeType.HAS_TILE, source=source, target=target)
        return edge
   