import arcadedb_embedded as arcadedb

from database.repository.world import WorldRepository
from map.generator import MapGenerator
from map.heightmap import HeightmapGenerator


class MapService:
    def __init__(self, database: arcadedb.Database) -> None:
        self._database = database
        self._world_repo = WorldRepository(database)

    def create(
        self,
        name: str,
        description: str,
        seed: int,
        size: int,
        major_count: int,
        major_radius_pct: int,
        detail_count: int,
        detail_radius_pct: int,
    ) -> None:
        self._world_repo.create_world(
            name=name,
            description=description,
            seed=seed,
            size=size,
            major_count=major_count,
            major_radius_pct=major_radius_pct,
            detail_count=detail_count,
            detail_radius_pct=detail_radius_pct,
        )
        tiles = MapGenerator(size=size, database=self._database).generate()
        HeightmapGenerator(
            seed=seed,
            size=size,
            major_count=major_count,
            major_radius_pct=major_radius_pct,
            detail_count=detail_count,
            detail_radius_pct=detail_radius_pct,
            database=self._database,
            tiles=tiles,
        ).generate()
