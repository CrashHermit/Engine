from arcadedb_embedded.graph import Vertex

from src.core.model.location import EntityData, LocationData, LocationState
from src.database.repository.location import LocationRepository


class LocationService:
    def __init__(self, locations: LocationRepository) -> None:
        self._locations = locations

    def get_state(self, location_id: str) -> LocationState | None:
        location = self._locations.get_location(location_id)
        if location is None:
            return None
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
