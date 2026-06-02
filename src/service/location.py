from arcadedb_embedded.graph import Vertex
import json
import logging

from src.core.model.entity import Danger, EntityKind, EntityStatus, ThreatPillar
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
        kind = EntityKind(entity.get(name="kind") or EntityKind.OBJECT.value)
        status, broken_pillar, clocks, returns_when = _resolution_from_json(
            entity.get(name="resolution")
        )
        return EntityData(
            id=entity.get(name="id") or "",
            name=entity.get(name="name") or "",
            description=entity.get(name="description") or "",
            scene_position=entity.get(name="scene_position") or "",
            kind=kind,
            danger=danger,
            threat_channels=channels,
            status=status,
            broken_pillar=broken_pillar,
            clocks=clocks,
            returns_when=returns_when,
        )

    def persist_entity_state(self, entities: list[EntityData]) -> None:
        """Write each entity's de-threat resolution state back to its vertex."""
        with self._base.transaction():
            for e in entities:
                if not e.id:
                    continue
                vertex = self._locations.get_entity(e.id)
                if vertex is not None:
                    self._locations.set_entity_resolution(vertex, _resolution_to_json(e))

    def remove_entity(self, entity_id: str) -> None:
        """Remove a defeated entity from the world."""
        self._logger.info("remove_entity id=%s", entity_id)
        with self._base.transaction():
            vertex = self._locations.get_entity(entity_id)
            if vertex is not None:
                self._locations.remove_entity(vertex)


def _resolution_to_json(entity: EntityData) -> str:
    return json.dumps(
        {
            "status": entity.status.value,
            "broken_pillar": entity.broken_pillar.value if entity.broken_pillar else None,
            "clocks": {p.value: f for p, f in entity.clocks.items()},
            "returns_when": entity.returns_when,
        }
    )


def _resolution_from_json(
    raw: str | None,
) -> tuple[EntityStatus, ThreatPillar | None, dict[ThreatPillar, int], str]:
    if not raw:
        return EntityStatus.ACTIVE, None, {}, ""
    data = json.loads(raw)
    status = EntityStatus(data.get("status") or EntityStatus.ACTIVE.value)
    broken = data.get("broken_pillar")
    broken_pillar = ThreatPillar(broken) if broken else None
    clocks = {ThreatPillar(p): int(f) for p, f in (data.get("clocks") or {}).items()}
    return status, broken_pillar, clocks, data.get("returns_when") or ""
