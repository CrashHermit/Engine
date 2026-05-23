from datetime import timezone
from datetime import datetime
import uuid
from database.repository.base import BaseRepository
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType

class LocationRepository(BaseRepository):

    def get_location(self, id: str) -> Vertex | None:
        return self.get_vertex(type_name=VertexType.LOCATION, id=id)

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