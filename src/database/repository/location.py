from datetime import timezone
from datetime import datetime
import uuid
from database.repository.base import BaseRepository
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType

class LocationRepository(BaseRepository):

    def get_location(self, name: str) -> Vertex | None:
        return self.get_vertex(type_name=VertexType.LOCATION, name=name)

    def create_location(self, name: str, description: str) -> Vertex:
        location: Vertex = self.create_vertex(
            type_name=VertexType.LOCATION,
            name=name,
            id=str(uuid.uuid4()),
            description=description,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        return location

    def get_or_create_location(self, name: str, description: str) -> Vertex:
        location: Vertex | None = self.get_location(name=name)
        if location is not None:
            return location

        return self.create_location(name=name, description=description)