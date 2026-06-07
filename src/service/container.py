from __future__ import annotations

import arcadedb_embedded
from arcadedb_embedded.core import Database

from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.repository.location import LocationRepository
from src.database.repository.message import MessageRepository
from src.database.repository.world import WorldRepository
from src.service.character import CharacterService
from src.service.graph import GraphService
from src.service.location import LocationService
from src.service.message import MessageService
from src.service.time import TimeService


class ServiceContainer:
    """Hold every in-session service for a single open world database.

    Built once when a world is opened (see WorldSessionFactory) and handed to
    TUI screens (and other integration code). Callers talk to services — never
    to repositories directly.
    Graph nodes do not receive a ServiceContainer; they read/write GraphState only.
    Side effects are applied post-ainvoke by the TUI via services (see decision #21).
    """

    def __init__(
        self,
        database: arcadedb_embedded.Database,
        *,
        world_name: str,
        graph_service: GraphService,
    ) -> None:
        self._database: Database = database
        self.world_name: str = world_name
        self.graph_service: GraphService = graph_service

        base: BaseRepository = BaseRepository(database)
        characters: CharacterRepository = CharacterRepository(base)
        worlds: WorldRepository = WorldRepository(base)
        locations: LocationRepository = LocationRepository(base)
        messages: MessageRepository = MessageRepository(base)

        self.character: CharacterService = CharacterService(base, characters, worlds)
        self.location: LocationService = LocationService(base, locations, characters)
        self.message: MessageService = MessageService(base, messages)
        self.time: TimeService = TimeService(worlds)
