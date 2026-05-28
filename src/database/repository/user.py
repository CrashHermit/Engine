from arcadedb_embedded.graph import Vertex

from src.core.model.database import VertexType
from src.database.repository.base import BaseRepository


class UserRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base

    def get_user(self) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.USER, id="user")

    def create_user(self) -> Vertex:
        return self._base.create_vertex(type_name=VertexType.USER, id="user")

    def get_or_create_user(self) -> Vertex:
        user = self.get_user()
        if user is not None:
            return user
        return self.create_user()
