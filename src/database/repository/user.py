import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Vertex

from core.model.database import VertexType
from database.repository.base import BaseRepository


class UserRepository:
    def __init__(self, database: arcadedb.Database) -> None:
        self._base = BaseRepository(database)

    def transaction(self):
        return self._base.transaction()

    def get_user(self) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.USER, id="user")

    def create_user(self) -> Vertex:
        return self._base.create_vertex(type_name=VertexType.USER, id="user")

    def get_or_create_user(self) -> Vertex:
        user = self.get_user()
        if user is not None:
            return user
        return self.create_user()
