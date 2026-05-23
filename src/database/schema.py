from arcadedb_embedded.schema import Schema
from arcadedb_embedded.core import Database
import arcadedb_embedded as arcadedb
from core.model.database import VertexType
from core.model.database import EdgeType

PROPERTY_TYPES: dict[str, arcadedb.PropertyType] = {
    "id": arcadedb.PropertyType.STRING,
    "name": arcadedb.PropertyType.STRING,
    "description": arcadedb.PropertyType.STRING,
    "role": arcadedb.PropertyType.STRING,
    "content": arcadedb.PropertyType.STRING,
    "tags": arcadedb.PropertyType.STRING,
    "created_at": arcadedb.PropertyType.DATETIME,
    "updated_at": arcadedb.PropertyType.DATETIME,
    "invalidated_at": arcadedb.PropertyType.DATETIME,
}

BASELINE_PROPERTIES: list[str] = ["id", "created_at", "updated_at", "invalidated_at"]

VERTEX_SCHEMA: dict[VertexType, list[str]] = {
    VertexType.USER: [],
    VertexType.LOCATION: ["name", "description"],
    VertexType.PART: ["name", "tags"],
    VertexType.MESSAGE: ["role", "content"],
    VertexType.CHARACTER: ["name", "description"],
    VertexType.ATTRIBUTES: [],
    VertexType.CORPUS: ["corpus_score"],
    VertexType.MENS: ["mens_score"],
    VertexType.ANIMA: ["anima_score"],
}

EDGE_SCHEMA: dict[EdgeType, list[str]] = {
    EdgeType.HAS_ATTRIBUTES: [],
    EdgeType.HAS_CORPUS: [],
    EdgeType.HAS_MENS: [],
    EdgeType.HAS_ANIMA: [],
}


class SchemaManager:
    def __init__(self, database: arcadedb.Database) -> None:
        self.database: Database = database

    def ensure(self) -> None:
        schema: Schema = self.database.schema
        for vertex_type in VertexType:
            self._vertex(schema=schema, name=vertex_type, properties=VERTEX_SCHEMA.get(vertex_type, []))
        for edge_type in EdgeType:
            self._edge(schema=schema, name=edge_type, properties=EDGE_SCHEMA.get(edge_type, []))
        self._indexes(schema)

    def _vertex(self, schema: Schema, name: VertexType, properties: list[str]) -> None:
        type_name = name.value
        schema.get_or_create_vertex_type(name=type_name)
        for prop in BASELINE_PROPERTIES + properties:
            schema.get_or_create_property(
                type_name=type_name,
                property_name=prop,
                property_type=PROPERTY_TYPES[prop],
            )

    def _edge(self, schema: Schema, name: EdgeType, properties: list[str]) -> None:
        type_name = name.value
        schema.get_or_create_edge_type(name=type_name)
        for prop in BASELINE_PROPERTIES + properties:
            schema.get_or_create_property(
                type_name=type_name,
                property_name=prop,
                property_type=PROPERTY_TYPES[prop],
            )

    def _indexes(self, schema: Schema) -> None:
        for vertex_type in VertexType:
            schema.get_or_create_index(
                type_name=vertex_type.value,
                property_names=["id"],
                unique=True,
            )
        for edge_type in EdgeType:
            schema.get_or_create_index(
                type_name=edge_type.value,
                property_names=["id"],
                unique=True,
            )
