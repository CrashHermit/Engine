from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Edge, Vertex

from core.model.database import EdgeType, VertexType


class BaseRepository:
    def __init__(self, database: arcadedb.Database) -> None:
        self._database: arcadedb.Database = database
        self._in_transaction: bool = False
        self._now: datetime | None = None

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        if self._in_transaction:
            yield
            return
        self._in_transaction = True
        self._now = datetime.now(tz=timezone.utc)
        try:
            with self._database.transaction():
                yield
        finally:
            self._in_transaction = False
            self._now = None

    def _current_time(self) -> datetime:
        return self._now if self._now is not None else datetime.now(tz=timezone.utc)

    ############################################################################
    # Vertex operations
    ############################################################################

    def create_vertex(self, type_name: VertexType, **properties: Any) -> Vertex:
        now = self._current_time()
        properties.setdefault("created_at", now)
        properties.setdefault("updated_at", now)

        def _do(db: arcadedb.Database) -> Vertex:
            vertex: Vertex = db.new_vertex(type_name=type_name.value)
            for name, value in properties.items():
                vertex.set(name=name, value=value)
            vertex.save()
            return vertex

        if self._in_transaction:
            return _do(self._database)
        with self._database.transaction():
            return _do(self._database)

    def create_vertices(self, type_name: VertexType, items: list[dict[str, Any]]) -> list[Vertex]:
        with self.transaction():
            return [self.create_vertex(type_name=type_name, **item) for item in items]

    def get_vertex(self, type_name: VertexType, id: str) -> Vertex | None:
        return self._database.lookup_by_key(
            type_name=type_name.value, keys=["id"], values=[id]
        )

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

    def get_vertex_out_edges(self, vertex: Vertex, type_name: EdgeType) -> list[Edge]:
        return vertex.get_out_edges(labels=type_name.value)

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

        def _do() -> Edge:
            edge = source.new_edge(label=type_name.value, target=target, **properties)
            edge.save()
            return edge

        if self._in_transaction:
            return _do()
        with self._database.transaction():
            return _do()

    def create_edges(self, type_name: EdgeType, items: list[dict[str, Any]]) -> list[Edge]:
        with self.transaction():
            return [self.create_edge(type_name=type_name, **item) for item in items]

    def get_edge(self, type_name: EdgeType, id: str) -> Edge | None:
        record = self._database.lookup_by_key(
            type_name=type_name.value,
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
