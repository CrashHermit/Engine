import arcadedb_embedded as arcadedb

from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.repository.location import LocationRepository
from src.database.repository.message import MessageRepository
from src.database.repository.world import WorldRepository
from src.services.character import CharacterService
from src.services.location import LocationService
from src.services.message import MessageService
from src.services.graph import GraphService


class ServiceContainer:
    """Holds every in-session service for a single open world database.

    Built once when a world is opened (see WorldSessionFactory) and handed to
    the TUI screens and graph nodes, which only ever talk to services — never to
    repositories directly.
    """

    def __init__(
        self,
        database: arcadedb.Database,
        *,
        world_name: str,
        graph_service: GraphService,
    ) -> None:
        self._database = database
        self.world_name = world_name
        self.graph_service = graph_service

        base = BaseRepository(database)
        characters = CharacterRepository(base)
        worlds = WorldRepository(base)
        locations = LocationRepository(base)
        messages = MessageRepository(base)

        self.character = CharacterService(base, characters, worlds)
        self.location = LocationService(base, locations, characters)
        self.message = MessageService(base, messages)
