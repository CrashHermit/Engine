from arcadedb_embedded.graph import Vertex
import logging

from src.core.mechanic.effect import capacity_for_danger
from src.core.mechanic.harm import WoundPool
from src.core.model.entity import Danger
from src.core.model.location import EntityData, LocationData, LocationState
from src.core.model.threat import Channel
from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.repository.location import LocationRepository


class LocationService:
    def __init__(
        self,
        base: BaseRepository,
        locations: LocationRepository,
        characters: CharacterRepository,
    ) -> None:
        self._logger = logging.getLogger("engine.service.location")
        self._base = base
        self._locations = locations
        self._characters = characters

    def get_state_for_character(self, character_id: str) -> LocationState | None:
        """Where the character currently is, plus its exits and entities. Returns
        None only when the character has no location yet."""
        character = self._characters.get_character(character_id)
        if character is None:
            raise ValueError(f"Character not found: {character_id}")
        location = self._characters.get_current_location(character)
        state = self._build_state(location) if location is not None else None
        self._logger.debug("get_state_for_character id=%s found=%s", character_id, state is not None)
        return state

    def move_character(self, character_id: str, destination_id: str) -> LocationState | None:
        """Move the character to a connected location and return the new state."""
        self._logger.info("move_character id=%s destination=%s", character_id, destination_id)
        character = self._characters.get_character(character_id)
        if character is None:
            raise ValueError(f"Character not found: {character_id}")
        destination = self._locations.get_location(destination_id)
        if destination is None:
            raise ValueError(f"Location not found: {destination_id}")
        with self._base.transaction():
            self._characters.move_character(character, destination)
        return self._build_state(destination)

    def _build_state(self, location: Vertex) -> LocationState:
        return LocationState(
            location=self._to_location_data(location),
            neighbors=[self._to_location_data(n) for n in self._locations.get_neighbors(location)],
            entities=[self._to_entity_data(e) for e in self._locations.get_entities(location)],
        )

    def _to_location_data(self, location: Vertex) -> LocationData:
        return LocationData(
            id=location.get(name="id"),
            name=location.get(name="name") or "",
            description=location.get(name="description") or "",
        )

    def _to_entity_data(self, entity: Vertex) -> EntityData:
        channels_csv = entity.get(name="threat_channels") or ""
        channels = frozenset(
            Channel(c) for c in (s.strip() for s in channels_csv.split(",")) if c
        )
        danger = Danger(entity.get(name="danger") or Danger.STANDARD.value)
        capacity = entity.get(name="wound_capacity") or capacity_for_danger(danger)
        filled = entity.get(name="wound_filled") or 0
        return EntityData(
            id=entity.get(name="id") or "",
            name=entity.get(name="name") or "",
            description=entity.get(name="description") or "",
            scene_position=entity.get(name="scene_position") or "",
            danger=danger,
            threat_channels=channels,
            wound=WoundPool(capacity=capacity, filled=filled),
        )

    def persist_entity_wounds(self, entities: list[EntityData]) -> None:
        """Write each entity's clock fill back to its vertex (post-turn)."""
        with self._base.transaction():
            for e in entities:
                if not e.id:
                    continue
                vertex = self._locations.get_entity(e.id)
                if vertex is not None:
                    self._locations.set_entity_wounds(vertex, e.wound.filled)

    def remove_entity(self, entity_id: str) -> None:
        """Remove a defeated entity from the world."""
        self._logger.info("remove_entity id=%s", entity_id)
        with self._base.transaction():
            vertex = self._locations.get_entity(entity_id)
            if vertex is not None:
                self._locations.remove_entity(vertex)
