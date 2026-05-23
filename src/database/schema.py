from arcadedb_embedded.schema import Schema
from arcadedb_embedded.schema import PropertyType
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

VERTEX_SCHEMA: dict[VertexType, list[str]] = {
    VertexType.USER: ["id", "created_at"],
    VertexType.CHARACTER: ["id", "name", "created_at"],
    VertexType.LOCATION: ["id", "name", "description", "created_at"],
    VertexType.PART: ["id", "name", "tags", "created_at"],
    VertexType.MESSAGE: ["id", "role", "content", "created_at"],
    VertexType.OPENING: ["id"],
    VertexType.SOURCE: ["id"],
    VertexType.SINK: ["id"],
    VertexType.CHANNEL: ["id"],
    VertexType.MANIPULATOR: ["id"],
    VertexType.MOVEMENT: ["id"],
}


class SchemaManager:
    def __init__(self, database: arcadedb.Database) -> None:
        self.database: Database = database

    def ensure(self) -> None:
        schema: Schema = self.database.schema
        for vertex_type, properties in VERTEX_SCHEMA.items():
            self._vertex(schema=schema, name=vertex_type, properties=properties)
        for edge_type in EdgeType:
            self._edge(schema=schema, name=edge_type)
        self._indexes(schema)

    def _vertex(self, schema: Schema, name: VertexType, properties: list[str]) -> None:
        type_name = name.value
        schema.get_or_create_vertex_type(name=type_name)
        for prop in properties:
            schema.get_or_create_property(
                type_name=type_name,
                property_name=prop,
                property_type=PROPERTY_TYPES[prop],
            )

    def _edge(self, schema: Schema, name: EdgeType) -> None:
        type_name = name.value
        schema.get_or_create_edge_type(name=type_name)
        schema.get_or_create_property(
            type_name=type_name,
            property_name="id",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name=type_name,
            property_name="created_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )

    def _indexes(self, schema: Schema) -> None:
        for vertex_type in VertexType:
            schema.get_or_create_index(
                type_name=vertex_type.value,
                property_names=["id"],
                unique=True,
            )
