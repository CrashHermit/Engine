from src.database.repository.location import LocationRepository
from src.database.repository.tile import TileRepository
from src.database.repository.world import WorldRepository
from src.database.repository.base import BaseRepository
from arcadedb_embedded.core import Database
from src.core.model.database import EdgeType
from src.worldgen.data import WorldData
from src.worldgen.pipeline import WorldgenPipeline
from src.database.connection import DatabaseConnection
from src.database.schema import SchemaManager


class WorldService:
    def __init__(self, connection: DatabaseConnection) -> None:
        self._connection: DatabaseConnection = connection

    def create_world(
        self,
        name: str,
        description: str,
        seed: int,
        size: int,
        biome: str,
        temperature: float,
        precipitation: float,
        elevation: float,
    ) -> None:
        world_data: WorldData = WorldData(
            name=name,
            description=description,
            seed=seed,
            size=size,
            biome=biome,
            temperature=temperature,
            precipitation=precipitation,
            elevation=elevation,
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
                biome=biome,
                temperature=temperature,
                precipitation=precipitation,
                elevation=elevation,
            )
            tile_repo.create_tiles(world_data.tiles)

    # PROTOTYPE START
    def create_test_world(self) -> None:
        name = "Test World"
        db: Database = self._connection.create_database(name)
        SchemaManager(database=db).ensure()

        base: BaseRepository = BaseRepository(database=db)
        world_repo: WorldRepository = WorldRepository(base=base)
        location_repo: LocationRepository = LocationRepository(base=base)

        with base.transaction():
            world = world_repo.create_world(
                name=name,
                description="A small test dungeon for development.",
                seed=1234567890,
                size=7,
                biome="dungeon",
                temperature=0.0,
                precipitation=0.0,
                elevation=0.0,
            )
            center = location_repo.create_start_location()
            base.create_edge(type_name=EdgeType.HAS_START, source=world, target=center)
    # PROTOTYPE END

        