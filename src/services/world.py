from database.repository.location import LocationRepository
from src.database.repository.tile import TileRepository
from src.database.repository.world import WorldRepository
from src.database.repository.base import BaseRepository
from arcadedb_embedded.core import Database
from src.worldgen.data import WorldData
from src.worldgen.pipeline import WorldgenPipeline
from src.database.connection import DatabaseConnection
from src.database.schema import SchemaManager


class WorldService:
    def __init__(self, connection: DatabaseConnection) -> None:
        self._connection: DatabaseConnection = connection
        self._location_repo: LocationRepository = LocationRepository(base=BaseRepository(database=self._connection.database))

    def create_world(
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
        world_data: WorldData = WorldData(
            name=name,
            description=description,
            seed=seed,
            size=size,
            major_count=major_count,
            major_radius_pct=major_radius_pct,
            detail_count=detail_count,
            detail_radius_pct=detail_radius_pct,
        )

        pipeline: WorldgenPipeline = WorldgenPipeline()
        world_data: WorldData = pipeline.run(data=world_data)

        db: Database = self._connection.create_database(name)
        SchemaManager(database=db).ensure()

        base: BaseRepository = BaseRepository(database=db)
        world_repo: WorldRepository = WorldRepository(base=base)
        tile_repo: TileRepository = TileRepository(base=base)

        with base.transaction():
            world_repo.create_world(
                name=name,
                description=description,
                seed=seed,
                size=size,
                major_count=major_count,
                major_radius_pct=major_radius_pct,
                detail_count=detail_count,
                detail_radius_pct=detail_radius_pct,
            )
            tile_repo.create_tiles(world_data.tiles)

    def create_test_world(self) -> None:
        self.create_world(
            name="Test World",
            description="This is a test world",
            seed=1234567890,
            size=100,
            major_count=10,
            major_radius_pct=50,
            detail_count=10,
            detail_radius_pct=50,
        )

        