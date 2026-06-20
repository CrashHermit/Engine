from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.environment.ecology.biome import BiomeEnum
from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


class TileRepository:
    def __init__(self, base: BaseRepository) -> None:
        """Wrap a BaseRepository for tile-specific graph operations."""
        self._base: BaseRepository = base

    def create_tile_vertex(
        self,
        x: int,
        y: int,
    ) -> Vertex:
        """Create a tile vertex at the given grid coordinates."""

        return self._base.create_vertex(
            type_name=VertexType.TILE,
            x=x,
            y=y,
        )

    def create_has_tile_edge(
        self, source_vertex: Vertex, target_vertex: Vertex
    ) -> Edge:
        """Link a parent vertex to a tile via a HAS_TILE edge."""

        edge: Edge = self._base.create_edge(
            type_name=EdgeType.HAS_TILE, source=source_vertex, target=target_vertex
        )
        return edge

    def get_tile_vertex(self, id: str) -> Vertex | None:
        """Fetch a tile vertex by its unique id, or None if not found."""

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
        """Persist long-term climate and biome data on a tile vertex."""

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
        """Persist current weather conditions on a tile vertex."""

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
        """Persist river and lake flags on a tile vertex."""

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
        """Persist land/sea classification and landmass membership on a tile."""

        return self._base.update_vertex(
            vertex=tile_vertex,
            is_land=is_land,
            landmass_id=landmass_id,
        )

    def update_tile_vertex_ecology(
        self,
        tile_vertex: Vertex,
        savagery: float,
        alignment: float,
    ) -> Vertex:
        """Persist savagery and alignment scores for a tile's ecology."""

        return self._base.update_vertex(
            vertex=tile_vertex,
            savagery=savagery,
            alignment=alignment,
        )

    def get_tile_vertex_at(self, x: int, y: int) -> Vertex | None:
        """Look up a tile vertex by grid coordinates, or None if absent."""

        return self._base.lookup_vertex(
            type_name=VertexType.TILE, keys=["x", "y"], values=[x, y]
        )

    def get_tile_vertex_neighbors(self, tile_vertex: Vertex, size: int) -> list[Vertex]:
        """Return the eight adjacent tiles, wrapping at map edges via modulo.
        Raises LookupError if any expected neighbor tile is missing.
        """

        offsets: list[tuple[int, int]] = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
        ]

        x: int = int(tile_vertex.get(name="x"))
        y: int = int(tile_vertex.get(name="y"))

        neighbors: list[Vertex | None] = []

        for dx, dy in offsets:
            nx: int = (x + dx) % size
            ny: int = (y + dy) % size

            neighbor: Vertex | None = self.get_tile_vertex_at(x=nx, y=ny)

            if neighbor is None:
                raise LookupError(f"Missing tile at ({nx}, {ny})")

            neighbors.append(neighbor)

        return neighbors
