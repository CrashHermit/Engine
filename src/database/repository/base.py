from datetime import datetime, timezone
from typing import Any

import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Edge, Vertex

from core.model.database import EdgeType, VertexType


class BaseRepository:
    def __init__(self, database: arcadedb.Database) -> None:
        self._database: arcadedb.Database = database

    ############################################################################
    # Vertex operations
    ############################################################################

    def create_vertex(self, type_name: VertexType, **properties: Any) -> Vertex:
        with self._database.transaction():
            vertex: Vertex = self._database.new_vertex(type_name=type_name.value)
            for name, value in properties.items():
                vertex.set(name=name, value=value)
            vertex.save()
        return vertex

    def get_vertex(self, type_name: VertexType, id: str) -> Vertex | None:
        return self._database.lookup_by_key(
            type_name=type_name.value, keys=["id"], values=[id]
        )

    def update_vertex(self, vertex: Vertex, **properties: Any) -> None:
        mutable: Vertex = vertex.modify()
        for name, value in properties.items():
            mutable.set(name=name, value=value)
        mutable.save()

    def delete_vertex(self, vertex: Vertex) -> None:
        vertex.delete()

    def invalidate_vertex(self, vertex: Vertex) -> None:
        vertex.modify().set(
            name="invalidated_at",
            value=datetime.now(tz=timezone.utc),
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
        with self._database.transaction():
            edge = source.new_edge(label=type_name.value, target=target, **properties)
            edge.save()
        return edge

    def get_edge(self, type_name: EdgeType, id: str) -> Edge | None:
        record = self._database.lookup_by_key(
            type_name=type_name.value,
            keys=["id"],
            values=[id],
        )
        return record if isinstance(record, Edge) else None

    def update_edge(self, edge: Edge, **properties: Any) -> None:
        mutable: Edge = edge.modify()
        for name, value in properties.items():
            mutable.set(name=name, value=value)
        mutable.save()

    def delete_edge(self, edge: Edge) -> None:
        edge.delete()

    def invalidate_edge(self, edge: Edge) -> None:
        edge.modify().set(
            name="invalidated_at",
            value=datetime.now(tz=timezone.utc),
        ).save()
