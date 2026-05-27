from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository


class CharacterRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def get_user_characters(self, user: Vertex) -> list[Vertex]:
        edges: list[Edge] = user.get_out_edges(EdgeType.HAS_CHARACTER)
        return [edge.get_in() for edge in edges]

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

    def create_trait(self, character: Vertex, vertex_type: VertexType, edge_type: EdgeType) -> Vertex:
        trait: Vertex = self._base.create_vertex(type_name=vertex_type)
        self._base.create_edge(type_name=edge_type, source=character, target=trait)
        return trait

    def create_personality(self, character: Vertex, vertex_type: VertexType, edge_type: EdgeType) -> Vertex:
        personality: Vertex = self._base.create_vertex(type_name=vertex_type)
        self._base.create_edge(type_name=edge_type, source=character, target=personality)
        return personality

    def create_attribute(self, source: Vertex, value: int) -> Vertex:
        attribute: Vertex = self._base.create_vertex(type_name=VertexType.ATTRIBUTE, value=value)
        self._base.create_edge(type_name=EdgeType.HAS_ATTRIBUTE, source=source, target=attribute)
        return attribute

    def get_corpus(self, character: Vertex) -> Vertex:
        return character.get_out_edges(EdgeType.HAS_CORPUS)[0].get_in()

    def get_mens(self, character: Vertex) -> Vertex:
        return character.get_out_edges(EdgeType.HAS_MENS)[0].get_in()

    def get_anima(self, character: Vertex) -> Vertex:
        return character.get_out_edges(EdgeType.HAS_ANIMA)[0].get_in()

    def get_personality(self, character: Vertex) -> Vertex:
        mens: Vertex = self.get_mens(character)
        return mens.get_out_edges(EdgeType.HAS_PERSONALITY)[0].get_in()

    def get_attribute_value(self, node: Vertex) -> int:
        attribute: Vertex = node.get_out_edges(EdgeType.HAS_ATTRIBUTE)[0].get_in()
        return attribute.get(name="value")

    def set_attribute_value(self, node: Vertex, value: int) -> None:
        attribute: Vertex = node.get_out_edges(EdgeType.HAS_ATTRIBUTE)[0].get_in()
        self._base.update_vertex(vertex=attribute, value=value)

    def get_current_location(self, character: Vertex) -> Vertex | None:
        edges = character.get_out_edges(EdgeType.LOCATED_AT)
        return edges[0].get_in() if edges else None

    def place_character(self, character: Vertex, location: Vertex) -> None:
        self._base.create_edge(
            type_name=EdgeType.LOCATED_AT,
            source=character,
            target=location,
        )

    def move_character(self, character: Vertex, to_location: Vertex) -> None:
        for edge in character.get_out_edges(EdgeType.LOCATED_AT):
            self._base.delete_edge(edge)
        self._base.create_edge(
            type_name=EdgeType.LOCATED_AT,
            source=character,
            target=to_location,
        )
