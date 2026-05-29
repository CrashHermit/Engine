from langgraph.checkpoint.base import BaseCheckpointSaver
from src.services.graph import GraphService
from src.database.connection import DatabaseConnection
from src.database.schema import SchemaManager
from src.services.container import ServiceContainer


class WorldSessionFactory:
    """Long-lived factory that opens a world database and wires up a fresh
    ServiceContainer for that session. Holds the stable DatabaseConnection so
    callers only need to supply a world name."""

    def __init__(
        self,
        connection: DatabaseConnection,
        *,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._connection = connection
        self._checkpointer = checkpointer
        self._graph_service = GraphService(checkpointer=checkpointer)

    def open(self, world_name: str) -> ServiceContainer:
        database = self._connection.open_database(world_name)
        SchemaManager(database=database).ensure()
        return ServiceContainer(
            database=database,
            world_name=world_name,
            graph_service=self._graph_service,
        )
