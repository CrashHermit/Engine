from arcadedb_embedded.graph import Vertex


import uuid
from datetime import datetime, timezone

import arcadedb_embedded as arcadedb
from arcadedb_embedded import Vertex


class SessionRepository:
    def __init__(self, database: arcadedb.Database) -> None:
        self._database: arcadedb.Database = database

    def create(self) -> str:
        session_id: str = str(uuid.uuid4())
        now: datetime = datetime.now(tz=timezone.utc)
        with self._database.transaction():
            session: Vertex = self._database.new_vertex(type_name="SESSION")
            session.set(name="id", value=session_id)
            session.set(name="created_at", value=now)
            session.set(name="updated_at", value=now)
            session.save()
        return session_id

    def get(self, session_id: str) -> Vertex | None:
        return self._database.lookup_by_key(type_name="SESSION", keys=["id"], values=[session_id])
