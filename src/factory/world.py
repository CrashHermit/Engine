import arcadedb_embedded as arcadedb
from arcadedb_embedded import Edge, Vertex

from src.database.repository.base import BaseRepository
from src.database.repository.time import TimeRepository
from src.database.repository.world import WorldRepository
from src.database.schema import SchemaManager, EdgeType
from src.database.connection import DatabaseConnection
from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.pipeline import WorldgenPipeline
from worldgen.features import WorldData
from worldgen.fields import GridFields


class WorldFactory:
    def __init__(self, connection: DatabaseConnection) -> None:
        self._connection: DatabaseConnection = connection

    def create_world(self, name: str, size: int, seed: int config: WorldgenConfig):
        database: arcadedb.Database = self._connection.create_database(name=name)
        SchemaManager(database=database).ensure()

        base: BaseRepository = BaseRepository(database=database)
        world_repo: WorldRepository = WorldRepository(base=base)
        time_repo: TimeRepository = TimeRepository(base=base)

        world_vertex: Vertex = world_repo.create_world_vertex(name=name)
        time_vertex: Vertex = time_repo.create_time_vertex(elapsed_ticks=0)

        has_time_edge: Edge = base.create_edge(
            type_name=EdgeType.HAS_TIME, source=world_vertex, target=time_vertex
        )

        pipeline: WorldgenPipeline = WorldgenPipeline(config)
        world_data: WorldData = pipeline.run(seed=seed, size=size)

        grid_fields: GridFields = world_data.grid
