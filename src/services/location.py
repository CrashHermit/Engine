from arcadedb_embedded.graph import Vertex

from src.core.model.location import EntityData, LocationData, LocationState
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
        self._base = base
        self._locations = locations
        self._characters = characters

    def get_state_for_character(self, character_id: str) -> LocationState | None:
        """Where the character currently is, plus its exits and entities."""
        character = self._characters.get_character(character_id)
        if character is None:
            return None
        location = self._characters.get_current_location(character)
        return self._build_state(location) if location is not None else None

    def move_character(self, character_id: str, destination_id: str) -> LocationState | None:
        """Move the character to a connected location and return the new state."""
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
        return EntityData(
            name=entity.get(name="name") or "",
            description=entity.get(name="description") or "",
            scene_position=entity.get(name="scene_position") or "",
        )
