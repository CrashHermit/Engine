from datetime import datetime, timezone
import uuid
from arcadedb_embedded import Vertex

from database.repository.base import BaseRepository
from core.model.database import VertexType


class UserRepository(BaseRepository):
    
    def get_or_create(self) -> Vertex:
        user: Vertex | None = self.get_vertex(type_name=VertexType.USER, id="user")
        if user is not None:
            return user

        user: Vertex = self.create_vertex(
            type_name=VertexType.USER,
            name="user",
            id=str(uuid.uuid4()),
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        return user
