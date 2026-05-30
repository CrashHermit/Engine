import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.database import EdgeType, VertexType


class BaseRepository:
    def __init__(self, database: arcadedb.Database) -> None:
        self._database: arcadedb.Database = database
        self._now: datetime | None = None

    @contextmanager
    def transaction(self) -> Generator[None]:
        if self._database.is_transaction_active():
            yield
            return
        self._now = datetime.now(tz=UTC)
        try:
            with self._database.transaction():
                yield
        finally:
            self._now = None

    def _current_time(self) -> datetime:
        return self._now if self._now is not None else datetime.now(tz=UTC)

    ############################################################################
    # Vertex operations
    ############################################################################

    def create_vertex(self, type_name: VertexType, **properties: Any) -> Vertex:
        now = self._current_time()
        properties.setdefault("id", str(uuid.uuid4()))
        properties.setdefault("created_at", now)
        properties.setdefault("updated_at", now)
        with self.transaction():
            vertex: Vertex = self._database.new_vertex(type_name=type_name)
            for name, value in properties.items():
                vertex.set(name=name, value=value)
            vertex.save()
        return vertex

    def create_vertices(self, type_name: VertexType, items: list[dict[str, Any]]) -> list[Vertex]:
        with self.transaction():
            return [self.create_vertex(type_name=type_name, **item) for item in items]

    def get_vertex(self, type_name: VertexType, id: str) -> Vertex | None:
        return self._database.lookup_by_key(type_name=type_name, keys=["id"], values=[id])

    def update_vertex(self, vertex: Vertex, **properties: Any) -> None:
        properties.setdefault("updated_at", self._current_time())
        mutable: Vertex = vertex.modify()
        for name, value in properties.items():
            mutable.set(name=name, value=value)
        mutable.save()

    def delete_vertex(self, vertex: Vertex) -> None:
        vertex.delete()

    def invalidate_vertex(self, vertex: Vertex) -> None:
        vertex.modify().set(
            name="invalidated_at",
            value=self._current_time(),
        ).save()

    ############################################################################
    # Edge operations
    ############################################################################

    def create_edge(
        self,
        type_name: EdgeType,
        source: Vertex,
        target: Vertex,
        **properties: Any,
    ) -> Edge:
        now = self._current_time()
        properties.setdefault("created_at", now)
        properties.setdefault("updated_at", now)

        with self.transaction():
            return source.new_edge(label=type_name, target=target, **properties)

    def create_edges(self, type_name: EdgeType, items: list[dict[str, Any]]) -> list[Edge]:
        with self.transaction():
            return [self.create_edge(type_name=type_name, **item) for item in items]

    def get_edge(self, type_name: EdgeType, id: str) -> Edge | None:
        record = self._database.lookup_by_key(
            type_name=type_name,
            keys=["id"],
            values=[id],
        )
        return record if isinstance(record, Edge) else None

    def update_edge(self, edge: Edge, **properties: Any) -> None:
        properties.setdefault("updated_at", self._current_time())
        mutable: Edge = edge.modify()
        for name, value in properties.items():
            mutable.set(name=name, value=value)
        mutable.save()

    def delete_edge(self, edge: Edge) -> None:
        edge.delete()

    def invalidate_edge(self, edge: Edge) -> None:
        edge.modify().set(
            name="invalidated_at",
            value=self._current_time(),
        ).save()

    ############################################################################
    # Query operations
    ############################################################################

    def list_vertices(self, type_name: VertexType) -> list[Vertex]:
        results = self._database.query("cypher", f"MATCH (n:{type_name}) RETURN n")
        return [v for r in results if (v := r.get_vertex()) is not None]
