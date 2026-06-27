"""KNOWN-BROKEN, OUT OF SCOPE for the worldgen redesign.

This module predates the worldgen rebuild and still imports the old
``src.worldgen.data`` vocabulary and persistence shape.  The redesign stopped
at producing :class:`src.worldgen.features.WorldData`; wiring it through to the
database is the *next* round.  That round starts here: update this service and
the ``TileRepository`` schema to persist the new ``GridFields`` columns
(temperature, sst, precipitation, discharge, river_id, lake_id, savagery,
magic_strength/channels, biome_weights, region_id).
"""

import json

from arcadedb_embedded.core import Database
from arcadedb_embedded.graph import Vertex

from src.core.model.database import EdgeType
from src.database.connection import DatabaseConnection
from src.database.repository.base import BaseRepository
from src.database.repository.location import LocationRepository
from src.database.repository.tile import TileRepository
from src.database.repository.world import WorldRepository
from src.database.schema import SchemaManager
from src.worldgen.data import DungeonData, WorldData
from src.worldgen.pipeline import WorldgenPipeline


class WorldService:
    """Bootstrap a new world: create the database, run worldgen, and persist.

    Unlike in-session services it owns database and schema creation, so it is
    constructed from the DatabaseConnection directly rather than from a
    ServiceContainer.
    """

    def __init__(self, connection: DatabaseConnection) -> None:
        self._connection: DatabaseConnection = connection

    def create_world():
        
