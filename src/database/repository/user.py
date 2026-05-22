from datetime import datetime, timezone

from arcadedb_embedded import Vertex

from database.repository.base import BaseRepository


class UserRepository(BaseRepository):
    _USER_ID = "user"

    def get_or_create(self) -> Vertex:
        user: Vertex | None = self._database.lookup_by_key(
            type_name="USER", keys=["id"], values=[self._USER_ID]
        )
        if user is not None:
            return user

        with self._database.transaction():
            user = self._database.new_vertex(type_name="USER")
            user.set(name="id", value=self._USER_ID)
            user.set(name="created_at", value=datetime.now(tz=timezone.utc))
            user.save()

        return user
