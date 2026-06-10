from __future__ import annotations

from arcadedb_embedded.graph import Edge, Vertex

from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository

# Edges from a character into the sub-structure it exclusively owns. Deleting a
# character cascades along these (but never along LOCATED_AT, which points at a
# shared location the character does not own).
_OWNED_EDGES: list[EdgeType] = [
    EdgeType.HAS_CORPUS,
    EdgeType.HAS_MENS,
    EdgeType.HAS_ANIMA,
    EdgeType.HAS_STRESS,
    EdgeType.HAS_TRAUMA,
    EdgeType.HAS_PERSONALITY,
    EdgeType.HAS_EXTRAVERSION,
    EdgeType.HAS_OPENNESS,
    EdgeType.HAS_NEUROTICISM,
    EdgeType.HAS_AGREEABLENESS,
    EdgeType.HAS_CONSCIENTIOUSNESS,
    EdgeType.HAS_ATTRIBUTE,
]


class CharacterRepository:
    def __init__(self, base: BaseRepository) -> None:
        self._base: BaseRepository = base

    def create_character(self, name: str, description: str) -> Vertex:
        return self._base.create_vertex(
            type_name=VertexType.CHARACTER,
            name=name,
            description=description,
        )

    def add_node(
        self, source: Vertex, vertex_type: VertexType, edge_type: EdgeType
    ) -> Vertex:
        node: Vertex = self._base.create_vertex(type_name=vertex_type)
        self._base.create_edge(type_name=edge_type, source=source, target=node)
        return node

    def add_attribute(self, source: Vertex, value: int) -> Vertex:
        attribute: Vertex = self._base.create_vertex(
            type_name=VertexType.ATTRIBUTE, value=value
        )
        self._base.create_edge(
            type_name=EdgeType.HAS_ATTRIBUTE, source=source, target=attribute
        )
        return attribute

    def delete_character(self, character: Vertex) -> None:
        children: list[Vertex] = [
            edge.get_in()
            for edge_type in _OWNED_EDGES
            for edge in character.get_out_edges(edge_type)
        ]
        for child in children:
            self.delete_character(character=child)
        self._base.delete_vertex(vertex=character)

    def list_characters(self) -> list[Vertex]:
        return self._base.list_vertices(type_name=VertexType.CHARACTER)

    def get_character(self, id: str) -> Vertex | None:
        return self._base.get_vertex(type_name=VertexType.CHARACTER, id=id)

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

    def get_trait_value(self, personality: Vertex, edge_type: EdgeType) -> int:
        trait = personality.get_out_edges(edge_type)[0].get_in()
        return self.get_attribute_value(trait)

    def get_current_location(self, character: Vertex) -> Vertex | None:
        edges: list[Edge] = character.get_out_edges(EdgeType.LOCATED_AT)
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

    def add_economy(self, character: Vertex) -> None:
        for vertex_type, edge_type in (
            (VertexType.STRESS, EdgeType.HAS_STRESS),
            (VertexType.TRAUMA, EdgeType.HAS_TRAUMA),
        ):
            node = self.add_node(character, vertex_type, edge_type)
            self.add_attribute(node, 0)

    def get_stress(self, character: Vertex) -> int:
        return self._economy_value(character, EdgeType.HAS_STRESS)

    def get_trauma(self, character: Vertex) -> int:
        return self._economy_value(character, EdgeType.HAS_TRAUMA)

    def set_stress(self, character: Vertex, value: int) -> None:
        node = self._ensure_economy_node(
            character, VertexType.STRESS, EdgeType.HAS_STRESS
        )
        self.set_attribute_value(node, value)

    def set_trauma(self, character: Vertex, value: int) -> None:
        node = self._ensure_economy_node(
            character, VertexType.TRAUMA, EdgeType.HAS_TRAUMA
        )
        self.set_attribute_value(node, value)

    def _economy_value(self, character: Vertex, edge_type: EdgeType) -> int:

        edges = character.get_out_edges(edge_type)
        return self.get_attribute_value(edges[0].get_in()) if edges else 0

    def _ensure_economy_node(
        self, character: Vertex, vertex_type: VertexType, edge_type: EdgeType
    ) -> Vertex:
        edges = character.get_out_edges(edge_type)
        if edges:
            return edges[0].get_in()
        node = self.add_node(character, vertex_type, edge_type)
        self.add_attribute(node, 0)
        return node
