import uuid
from datetime import datetime, timezone

from arcadedb_embedded import Vertex

from core.model.message import Message
from database.repository.base import BaseRepository


class MessageRepository(BaseRepository):
    def get_history(self) -> list[Message]:
        user: Vertex | None = self._database.lookup_by_key(
            type_name="USER", keys=["id"], values=["user"]
        )
        if user is None:
            return []

        edges = list(user.get_out_edges("HAS_MESSAGE"))
        if not edges:
            return []

        messages: list[Message] = []
        current: Vertex = edges[0].get_in()
        while True:
            messages.append(Message(role=current.get("role"), content=current.get("content")))
            next_edges = list(current.get_out_edges("NEXT_MESSAGE"))
            if not next_edges:
                break
            current = next_edges[0].get_in()

        return messages

    def append(self, messages: list[Message]) -> None:
        if not messages:
            return

        user: Vertex | None = self._database.lookup_by_key(
            type_name="USER", keys=["id"], values=["user"]
        )
        if user is None:
            raise ValueError("User not found")

        now = datetime.now(tz=timezone.utc)

        with self._database.transaction():
            existing_edges = list(user.get_out_edges("HAS_MESSAGE"))
            tail: Vertex | None = None

            if existing_edges:
                tail = existing_edges[0].get_in()
                while True:
                    next_edges = list(tail.get_out_edges("NEXT_MESSAGE"))
                    if not next_edges:
                        break
                    tail = next_edges[0].get_in()

            for msg in messages:
                vertex: Vertex = self._database.new_vertex(type_name="MESSAGE")
                vertex.set(name="id", value=str(uuid.uuid4()))
                vertex.set(name="role", value=msg.role)
                vertex.set(name="content", value=msg.content)
                vertex.set(name="created_at", value=now)
                vertex.save()

                if tail is None:
                    edge = user.new_edge("HAS_MESSAGE", vertex)
                    edge.set(name="id", value=str(uuid.uuid4()))
                    edge.set(name="created_at", value=now)
                    edge.save()
                else:
                    edge = tail.new_edge("NEXT_MESSAGE", vertex)
                    edge.set(name="id", value=str(uuid.uuid4()))
                    edge.set(name="created_at", value=now)
                    edge.save()

                tail = vertex
