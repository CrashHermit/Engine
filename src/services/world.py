from database.connection import DatabaseConnection
from database.schema import SchemaManager
from database.repository.base import BaseRepository
from database.repository.world import WorldRepository
from database.repository.tile import TileRepository
from worldgen.data import WorldData
from worldgen.pipeline import WorldgenPipeline
from worldgen.stages.grid import GridStage


class WorldService:
    def __init__(self, connection: DatabaseConnection) -> None:
        self._connection = connection

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
        db = self._connection.create_database(name)
        SchemaManager(db).ensure()

        world_data = WorldData(
            name=name,
            description=description,
            seed=seed,
            size=size,
            major_count=major_count,
            major_radius_pct=major_radius_pct,
            detail_count=detail_count,
            detail_radius_pct=detail_radius_pct,
        )

        pipeline = WorldgenPipeline(stages=[GridStage(size=size)])
        world_data = pipeline.run(world_data)

        base = BaseRepository(db)
        world_repo = WorldRepository(base)
        tile_repo = TileRepository(base)

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
