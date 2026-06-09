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

    def update_tile_vertex_climate(
        self,
        tile_vertex: Vertex,
        climate_temperature: float,
        climate_precipitation: float,
        climate_wind_u: float,
        climate_wind_v: float,
        climate_wind_magnitude: float,
        biomes: list[BiomeEnum],
    ) -> Vertex:
        return self._base.update_vertex(
            vertex=tile_vertex,
            climate_temperature=climate_temperature,
            climate_precipitation=climate_precipitation,
            climate_wind_u=climate_wind_u,
            climate_wind_v=climate_wind_v,
            climate_wind_magnitude=climate_wind_magnitude,
            biomes=biomes,
        )

    def update_tile_vertex_weather(
        self,
        tile_vertex: Vertex,
        weather_temperature: float,
        weather_precipitation: float,
        weather_wind_u: float,
        weather_wind_v: float,
        weather_wind_magnitude: float,
    ) -> Vertex:
        return self._base.update_vertex(
            vertex=tile_vertex,
            weather_temperature=weather_temperature,
            weather_precipitation=weather_precipitation,
            weather_wind_u=weather_wind_u,
            weather_wind_v=weather_wind_v,
            weather_wind_magnitude=weather_wind_magnitude,
        )

    def update_tile_vertex_hydrology(
        self,
        tile_vertex: Vertex,
        is_river: bool,
        is_lake: bool,
    ) -> Vertex:
        return self._base.update_vertex(
            vertex=tile_vertex,
            is_river=is_river,
            is_lake=is_lake,
        )

    def update_tile_vertex_geology(
        self,
        tile_vertex: Vertex,
        is_land: bool,
        landmass_id: int,
    ) -> Vertex:
        return self._base.update_vertex(
            vertex=tile_vertex, 
            is_land=is_land, 
            landmass_id=landmass_id,
        )

    def create_tile_vertex(
        self, 
        x: int, 
        y: int, 
    ) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.TILE, 
            x=x, 
            y=y,
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
   