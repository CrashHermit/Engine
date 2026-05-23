from datetime import timezone
from datetime import datetime
from arcadedb_embedded import Vertex

from database.repository.base import BaseRepository
from core.model.database import VertexType


class UserRepository(BaseRepository):

    def get_user(self) -> Vertex | None:
        return self.get_vertex(type_name=VertexType.USER, id="user")

    def create_user(self) -> Vertex:
        user: Vertex = self.create_vertex(
            type_name=VertexType.USER,
            id="user",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        return user

    def get_or_create_user(self) -> Vertex:
        user: Vertex | None = self.get_user()
        if user is not None:
            return user

        return self.create_user()