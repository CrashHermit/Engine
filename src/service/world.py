"""KNOWN-BROKEN, OUT OF SCOPE for the worldgen redesign.

This module predates the worldgen rebuild and still imports the old
``src.worldgen.data`` vocabulary and persistence shape.  The redesign stopped
at producing :class:`src.worldgen.features.WorldData`; wiring it through to the
database is the *next* round.  That round starts here: update this service and
the ``TileRepository`` schema to persist the new ``GridFields`` columns
(temperature, precipitation, discharge, river_id, lake_id, savagery,
magic_strength/valence/channels, biome_weights, region_id).
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

    def create_world(
        self,
        name: str,
        description: str,
        size: int,
    ) -> None:
        world_data: WorldData = WorldData(
            name=name,
            description=description,
            size=size,
        )
        world_data = WorldgenPipeline().run(data=world_data)

        db: Database = self._connection.create_database(name)
        SchemaManager(database=db).ensure()

        base: BaseRepository = BaseRepository(database=db)
        world_repo: WorldRepository = WorldRepository(base=base)
        tile_repo: TileRepository = TileRepository(base=base)
        location_repo: LocationRepository = LocationRepository(base=base)

        with base.transaction():
            world = world_repo.create_world(
                name=name,
                description=description,
                size=size,
            )
            tile_repo.create_tiles(world_data.tiles)

            start = self._seed_dungeon(location_repo, world_data.dungeon)
            if start is not None:
                base.create_edge(
                    type_name=EdgeType.HAS_START, source=world, target=start
                )

    def _seed_dungeon(
        self, location_repo: LocationRepository, dungeon: DungeonData | None
    ) -> Vertex | None:
        """Write the generated dungeon and return its center (the start location)."""
        if dungeon is None or not dungeon.locations:
            return None

        nodes = [
            location_repo.create_location_vertex(
                name=loc.name,
                description=loc.description,
                is_center=loc.is_center,
            )
            for loc in dungeon.locations
        ]

        for a, b in dungeon.connections:
            location_repo.connect_location_vertices(nodes[a], nodes[b])

        for node, loc in zip(nodes, dungeon.locations, strict=True):
            for entity in loc.entities:
                location_repo.create_entity(
                    location=node,
                    name=entity.name,
                    description=entity.description,
                    scene_position=entity.scene_position,
                    kind=entity.kind,
                    danger=entity.danger,
                    threat_channels=entity.threat_channels,
                    # Empty resolution => ACTIVE, no clocks; capacity derives
                    # from the profile (or danger when unauthored).
                    resolution="",
                    pillar_profile=json.dumps(entity.pillar_profile)
                    if entity.pillar_profile
                    else "",
                    disposition=entity.disposition,
                )

        for node, loc in zip(nodes, dungeon.locations, strict=True):
            if loc.is_center:
                return node
        return nodes[0]
