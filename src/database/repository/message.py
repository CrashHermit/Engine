import uuid

from arcadedb_embedded.graph import Vertex

from src.core.model.database import EdgeType, VertexType
from src.core.model.message import Message
from src.database.repository.base import BaseRepository


class MessageRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base

    def get_history(self) -> list[Message]:
        user = self._base.get_vertex(type_name=VertexType.USER, id="user")
        if user is None:
            return []

        edges = list(user.get_out_edges(EdgeType.HAS_MESSAGE))
        if not edges:
            return []

        messages: list[Message] = []
        current: Vertex = edges[0].get_in()
        while True:
            messages.append(Message(role=current.get("role"), content=current.get("content")))
            next_edges = list(current.get_out_edges(EdgeType.NEXT_MESSAGE))
            if not next_edges:
                break
            current = next_edges[0].get_in()

        return messages

    def append(self, messages: list[Message]) -> None:
        if not messages:
            return

        user = self._base.get_vertex(type_name=VertexType.USER, id="user")
        if user is None:
            raise ValueError("User not found")

        existing_edges = list(user.get_out_edges(EdgeType.HAS_MESSAGE))
        tail: Vertex | None = None

        if existing_edges:
            tail = existing_edges[0].get_in()
            while True:
                next_edges = list(tail.get_out_edges(EdgeType.NEXT_MESSAGE))
                if not next_edges:
                    break
                tail = next_edges[0].get_in()

        for msg in messages:
            vertex: Vertex = self._base.create_vertex(
                type_name=VertexType.MESSAGE,
                id=str(uuid.uuid4()),
                role=msg.role,
                content=msg.content,
            )
            edge_type = EdgeType.HAS_MESSAGE if tail is None else EdgeType.NEXT_MESSAGE
            source = user if tail is None else tail
            self._base.create_edge(
                type_name=edge_type,
                source=source,
                target=vertex,
                id=str(uuid.uuid4()),
            )
            tail = vertex
