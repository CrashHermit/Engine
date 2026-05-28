from arcadedb_embedded.schema import Schema
from arcadedb_embedded.core import Database
import arcadedb_embedded as arcadedb
from src.core.model.database import VertexType
from src.core.model.database import EdgeType

PROPERTY_TYPES: dict[str, arcadedb.PropertyType] = {
    "id": arcadedb.PropertyType.STRING,
    "name": arcadedb.PropertyType.STRING,
    "description": arcadedb.PropertyType.STRING,
    "role": arcadedb.PropertyType.STRING,
    "content": arcadedb.PropertyType.STRING,
    "value": arcadedb.PropertyType.INTEGER,
    "length": arcadedb.PropertyType.STRING,
    "width": arcadedb.PropertyType.STRING,
    "height": arcadedb.PropertyType.STRING,
    "shape": arcadedb.PropertyType.STRING,
    "status": arcadedb.PropertyType.STRING,
    "created_at": arcadedb.PropertyType.DATETIME,
    "updated_at": arcadedb.PropertyType.DATETIME,
    "invalidated_at": arcadedb.PropertyType.DATETIME,
    "q": arcadedb.PropertyType.INTEGER,
    "r": arcadedb.PropertyType.INTEGER,
    "elevation": arcadedb.PropertyType.INTEGER,
    "seed": arcadedb.PropertyType.INTEGER,
    "size": arcadedb.PropertyType.INTEGER,
    "major_count": arcadedb.PropertyType.INTEGER,
    "major_radius_pct": arcadedb.PropertyType.INTEGER,
    "detail_count": arcadedb.PropertyType.INTEGER,
    "detail_radius_pct": arcadedb.PropertyType.INTEGER,
    "direction": arcadedb.PropertyType.STRING,
    "is_center": arcadedb.PropertyType.BOOLEAN,
    "scene_position": arcadedb.PropertyType.STRING,
}

BASELINE_PROPERTIES: list[str] = ["id", "created_at", "updated_at", "invalidated_at"]

VERTEX_SCHEMA: dict[VertexType, list[str]] = {
    VertexType.USER: [],
    VertexType.LOCATION: ["name", "description", "is_center"],
    VertexType.PART: ["name", "length", "width", "height", "shape", "status", "description"],
    VertexType.OPENING: [],
    VertexType.SOURCE: [],
    VertexType.SINK: [],
    VertexType.STORAGE: [],
    VertexType.CHANNEL: [],
    VertexType.MANIPULATOR: [],
    VertexType.MOVEMENT: [],
    VertexType.CONTROLLABLE: [],
    VertexType.MESSAGE: ["role", "content"],
    VertexType.CHARACTER: ["name", "description"],
    VertexType.CORPUS: [],
    VertexType.MENS: [],
    VertexType.ANIMA: [],
    VertexType.PERSONALITY: [],
    VertexType.EXTRAVERSION: [],
    VertexType.OPENNESS: [],
    VertexType.NEUROTICISM: [],
    VertexType.AGREEABLENESS: [],
    VertexType.CONSCIENTIOUSNESS: [],
    VertexType.ATTRIBUTE: ["value"],
    VertexType.TILE: ["q", "r", "elevation"],
    VertexType.WORLD: ["name", "description", "seed", "size", "major_count", "major_radius_pct", "detail_count", "detail_radius_pct"],
    VertexType.ENTITY: ["name", "description", "scene_position"],  # PROTOTYPE
}

EDGE_SCHEMA: dict[EdgeType, list[str]] = {
    EdgeType.HAS_CORPUS: [],
    EdgeType.HAS_MENS: [],
    EdgeType.HAS_ANIMA: [],
    EdgeType.HAS_PERSONALITY: [],
    EdgeType.HAS_EXTRAVERSION: [],
    EdgeType.HAS_OPENNESS: [],
    EdgeType.HAS_NEUROTICISM: [],
    EdgeType.HAS_AGREEABLENESS: [],
    EdgeType.HAS_CONSCIENTIOUSNESS: [],
    EdgeType.HAS_ATTRIBUTE: [],
    EdgeType.HAS_PART: [],
    EdgeType.IS_SOURCE: [],
    EdgeType.IS_SINK: [],
    EdgeType.IS_STORAGE: [],
    EdgeType.IS_MANIPULATOR: [],
    EdgeType.IS_MOVEMENT: [],
    EdgeType.IS_OPENING: [],
    EdgeType.IS_CHANNEL: [],
    EdgeType.IS_CONTROLLABLE: [],
    EdgeType.ADJACENT: [],
    EdgeType.CONNECTS: [],
    EdgeType.LOCATED_AT: [],
    EdgeType.HAS_CHARACTER: [],
    EdgeType.HAS_START: [],  # PROTOTYPE: WORLD → LOCATION
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
        schema.get_or_create_vertex_type(name=name)
        for prop in BASELINE_PROPERTIES + properties:
            schema.get_or_create_property(
                type_name=name,
                property_name=prop,
                property_type=PROPERTY_TYPES[prop],
            )

    def _edge(self, schema: Schema, name: EdgeType, properties: list[str]) -> None:
        schema.get_or_create_edge_type(name=name)
        for prop in BASELINE_PROPERTIES + properties:
            schema.get_or_create_property(
                type_name=name,
                property_name=prop,
                property_type=PROPERTY_TYPES[prop],
            )

    def _indexes(self, schema: Schema) -> None:
        for vertex_type in VertexType:
            schema.get_or_create_index(
                type_name=vertex_type,
                property_names=["id"],
                unique=True,
            )
        for edge_type in EdgeType:
            schema.get_or_create_index(
                type_name=edge_type,
                property_names=["id"],
                unique=True,
            )
