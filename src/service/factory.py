from __future__ import annotations

import logging

from langgraph.checkpoint.base import BaseCheckpointSaver

from src.database.connection import DatabaseConnection
from src.database.schema import SchemaManager
from src.service.container import ServiceContainer
from src.service.graph import GraphService


class WorldSessionFactory:
    """Open a world database and wire up a fresh ServiceContainer for the session.

    Holds the stable DatabaseConnection so callers only need to supply a
    world name.
    """

    def __init__(
        self,
        connection: DatabaseConnection,
        *,
        checkpointer: BaseCheckpointSaver,
    ) -> None:
        self._logger = logging.getLogger("engine.service.world_session_factory")
        self._connection = connection
        self._checkpointer = checkpointer
        self._graph_service = GraphService(checkpointer=checkpointer)
        self._logger.info("world session factory initialized")

    def open(self, world_name: str) -> ServiceContainer:
        self._logger.info("opening world=%s", world_name)
        database = self._connection.open_database(world_name)
        SchemaManager(database=database).ensure()
        self._logger.debug("schema ensured world=%s", world_name)
        return ServiceContainer(
            database=database,
            world_name=world_name,
            graph_service=self._graph_service,
        )
