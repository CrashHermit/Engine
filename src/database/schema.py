import arcadedb_embedded as arcadedb
from arcadedb_embedded.schema import Schema


class SchemaManager:
    def __init__(self, database: arcadedb.Database) -> None:
        self.database: arcadedb.Database = database

    def ensure(self) -> None:
        schema: Schema = self.database.schema

        schema.get_or_create_vertex_type(name="SESSION")
        schema.get_or_create_property(
            type_name="SESSION",
            property_name="id",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name="SESSION",
            property_name="created_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="SESSION",
            property_name="updated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="SESSION",
            property_name="invalidated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )

        schema.get_or_create_vertex_type(name="MESSAGE")
        schema.get_or_create_property(
            type_name="MESSAGE",
            property_name="id",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name="MESSAGE",
            property_name="role",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name="MESSAGE",
            property_name="content",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name="MESSAGE",
            property_name="created_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="MESSAGE",
            property_name="updated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="MESSAGE",
            property_name="invalidated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )

        schema.get_or_create_edge_type(name="HAS_MESSAGE")
        schema.get_or_create_property(
            type_name="HAS_MESSAGE",
            property_name="id",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name="HAS_MESSAGE",
            property_name="created_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="HAS_MESSAGE",
            property_name="updated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="HAS_MESSAGE",
            property_name="invalidated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )

        schema.get_or_create_edge_type(name="NEXT_MESSAGE")
        schema.get_or_create_property(
            type_name="NEXT_MESSAGE",
            property_name="id",
            property_type=arcadedb.PropertyType.STRING,
        )
        schema.get_or_create_property(
            type_name="NEXT_MESSAGE",
            property_name="created_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="NEXT_MESSAGE",
            property_name="updated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )
        schema.get_or_create_property(
            type_name="NEXT_MESSAGE",
            property_name="invalidated_at",
            property_type=arcadedb.PropertyType.DATETIME,
        )

        self._ensure_indexes(schema)

    def _ensure_indexes(self, schema: Schema) -> None:
        schema.get_or_create_index(
            type_name="SESSION",
            property_names=["id"],
            unique=True,
        )
        schema.get_or_create_index(
            type_name="MESSAGE",
            property_names=["id"],
            unique=True,
        )
        schema.get_or_create_index(
            type_name="HAS_MESSAGE",
            property_names=["id"],
            unique=True,
        )
        schema.get_or_create_index(
            type_name="NEXT_MESSAGE",
            property_names=["id"],
            unique=True,
        )
