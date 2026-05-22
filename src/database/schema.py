import arcadedb_embedded as arcadedb
from arcadedb_embedded.schema import Schema


class SchemaManager:
    def __init__(self, database: arcadedb.Database) -> None:
        self.database = database

    def ensure(self) -> None:
        schema = self.database.schema
        self._vertex(schema, "USER", ["id", "created_at"])
        self._vertex(schema, "CHARACTER", ["id", "name", "created_at"])
        self._vertex(schema, "LOCATION", ["id", "name", "description", "created_at"])
        self._vertex(schema, "PART", ["id", "name", "tags", "created_at"])
        self._vertex(schema, "MESSAGE", ["id", "role", "content", "created_at"])
        self._vertex(schema, "OPENING", ["id"])
        self._vertex(schema, "SOURCE", ["id"])
        self._vertex(schema, "SINK", ["id"])
        self._vertex(schema, "CHANNEL", ["id"])
        self._vertex(schema, "MANIPULATOR", ["id"])
        self._vertex(schema, "MOVEMENT", ["id"])
        for edge in [
            "HAS_MESSAGE", "NEXT_MESSAGE", "LOCATED_AT",
            "CONNECTS", "ATTACHED_TO", "PRODUCES", "CONSUMES",
            "REQUIRES", "CONTROLS", "CONTAINS", "HAS_OPENING",
            "AFFORDS", "ENABLES",
        ]:
            self._edge(schema, edge)
        self._indexes(schema)

    def _vertex(self, schema: Schema, name: str, properties: list[str]) -> None:
        schema.get_or_create_vertex_type(name=name)
        type_map = {
            "id": arcadedb.PropertyType.STRING,
            "name": arcadedb.PropertyType.STRING,
            "description": arcadedb.PropertyType.STRING,
            "role": arcadedb.PropertyType.STRING,
            "content": arcadedb.PropertyType.STRING,
            "tags": arcadedb.PropertyType.STRING,
            "created_at": arcadedb.PropertyType.DATETIME,
        }
        for prop in properties:
            schema.get_or_create_property(
                type_name=name,
                property_name=prop,
                property_type=type_map[prop],
            )

    def _edge(self, schema: Schema, name: str) -> None:
        schema.get_or_create_edge_type(name=name)
        schema.get_or_create_property(
            type_name=name,
            property_name="id",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name=name,
            property_name="created_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )

    def _indexes(self, schema: Schema) -> None:
        for type_name in ["USER", "CHARACTER", "LOCATION", "PART", "MESSAGE"]:
            schema.get_or_create_index(type_name=type_name, property_names=["id"], unique=True)
