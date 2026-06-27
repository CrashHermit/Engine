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
        self._time = time

    def get_elapsed_ticks(self) -> int:
        """Return the current world time, in ticks (1 tick = 6 seconds)."""
        time_vertex: Vertex | None = self._time.get_time_vertex()
        if time_vertex is None:
            raise ValueError("Time vertex not found.")
        current_ticks: int = time_vertex.get(name="elapsed_ticks")
        return current_ticks

    def update_elapsed_ticks(self, delta_elapsed_ticks: int) -> Vertex:
        time_vertex: Vertex | None = self._time.get_time_vertex()
        if time_vertex is None:
            raise ValueError("Time vertex not found.")
        current_elapsed_ticks: int = time_vertex.get(name="elapsed_ticks")
        new_elapsed_ticks: int = current_elapsed_ticks + delta_elapsed_ticks
        if new_elapsed_ticks < 0:
            raise ValueError("World clock can't be negative.")
        updated_time_vertex: Vertex = self._time.update_time_vertex(
            vertex=time_vertex, elapsed_ticks=new_elapsed_ticks
        )
        return updated_time_vertex

    def create_time_vertex(self, elapsed_ticks: int) -> Vertex:
        """Create a new time vertex."""
        time_vertex: Vertex = self._time.create_time_vertex(elapsed_ticks=elapsed_ticks)
        return time_vertex

    def get_current_world_time(self) -> WorldDateTime:
        """Return the current world time as a WorldDateTime object."""
        elapsed_ticks: int = self.get_elapsed_ticks()
        seconds: int = elapsed_ticks * 6

        second: int = seconds % 60
        minute: int = (seconds // 60) % 60
        hour: int = (seconds // 3600) % 24
        day: int = (seconds // 86400) % 7
        week: int = (seconds // 604800) % 4
        month: int = (seconds // 2419200) % 12
        year: int = seconds // 29030400

        return WorldDateTime(
            year=year,
            month=month,
            week=week,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
        )

    def create_world():
        
