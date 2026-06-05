from __future__ import annotations

import logging

from src.database.connection import DatabaseConnection
from src.database.server import Server
from src.service.checkpoint import CheckpointService
from src.service.factory import WorldSessionFactory


class AppBootstrap:
    """Composition root for the application's infrastructure.

    Owns the embedded-database server, its connection, the checkpointer, and the
    WorldSessionFactory, and drives their start/stop lifecycle. Living here (not
    in `src/tui`) keeps the Textual layer free of any `src/database` imports —
    the app holds an AppBootstrap and reads `connection` / `factory` off it, but
    never touches infrastructure types directly (code-style §2 layer boundary).
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger("engine.bootstrap")
        self.server: Server | None = None
        self.connection: DatabaseConnection | None = None
        self.checkpoint: CheckpointService = CheckpointService()
        self.factory: WorldSessionFactory | None = None

    def start_server(self) -> None:
        """Start the embedded DB server and open a connection (synchronous)."""
        self._logger.info("starting database server")
        self.server = Server()
        self.server.start()
        self.connection = DatabaseConnection(self.server)

    async def start_session(self) -> WorldSessionFactory:
        """Start the checkpointer and build the world session factory.

        Must run after `start_server`; the checkpointer start is async.
        """
        await self.checkpoint.start()
        self.factory = WorldSessionFactory(
            self.connection,
            checkpointer=self.checkpoint.saver,
        )
        self._logger.info("world session factory ready")
        return self.factory

    async def stop(self) -> None:
        """Tear down the checkpointer and the database server."""
        await self.checkpoint.stop()
        if self.server is not None:
            self.server.stop()
            self.server = None
