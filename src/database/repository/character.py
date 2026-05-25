import arcadedb_embedded as arcadedb
from arcadedb_embedded.graph import Edge, Vertex

from core.model.database import EdgeType, VertexType
from database.repository.base import BaseRepository


class CharacterRepository:
    def __init__(self, database: arcadedb.Database) -> None:
        self._base = BaseRepository(database)

    def transaction(self):
        return self._base.transaction()

    def create_vertex(self, **kwargs) -> Vertex:
        return self._base.create_vertex(**kwargs)

    def create_edge(self, **kwargs) -> Edge:
        return self._base.create_edge(**kwargs)

    def get_user_characters(self, user: Vertex) -> list[Vertex]:
        edges: list[Edge] = user.get_out_edges(EdgeType.HAS_CHARACTER)
        return [edge.get_target() for edge in edges]

    def create_character(self, user: Vertex, name: str, description: str) -> Vertex:
        character: Vertex = self._base.create_vertex(
            type_name=VertexType.CHARACTER,
            name=name,
            description=description,
        )
        self._base.create_edge(
            type_name=EdgeType.HAS_CHARACTER,
            source=user,
            target=character,
        )
        return character

    def get_corpus(self, character: Vertex) -> Vertex:
        return character.get_out_edges(EdgeType.HAS_CORPUS)[0].get_target()

    def get_mens(self, character: Vertex) -> Vertex:
        return character.get_out_edges(EdgeType.HAS_MENS)[0].get_target()

    def get_anima(self, character: Vertex) -> Vertex:
        return character.get_out_edges(EdgeType.HAS_ANIMA)[0].get_target()

    def get_personality(self, character: Vertex) -> Vertex:
        mens: Vertex = self.get_mens(character)
        return mens.get_out_edges(EdgeType.HAS_PERSONALITY)[0].get_target()

    def get_attribute_value(self, node: Vertex) -> int:
        attribute: Vertex = node.get_out_edges(EdgeType.HAS_ATTRIBUTE)[0].get_target()
        return attribute.get(name="value")

    def set_attribute_value(self, node: Vertex, value: int) -> None:
        attribute: Vertex = node.get_out_edges(EdgeType.HAS_ATTRIBUTE)[0].get_target()
        self._base.update_vertex(vertex=attribute, value=value)
