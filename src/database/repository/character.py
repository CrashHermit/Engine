import uuid
from arcadedb_embedded.graph import Edge
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType, EdgeType
from database.repository.user import UserRepository


class CharacterRepository(UserRepository):

    def get_user_characters(self) -> list[Vertex]:
        user: Vertex | None = self.get_user()
        edges: list[Edge] | None = self.get_vertex_out_edges(vertex=user, type_name=EdgeType.HAS_CHARACTER)
        return [edge.get_target() for edge in edges]

    def create_character(self, name: str, description: str) -> Vertex:
        user: Vertex | None = self.get_user()
        character: Vertex = self.create_vertex(
            type_name=VertexType.CHARACTER,
            name=name,
            description=description,
        )
        self.create_edge(
            type_name=EdgeType.HAS_CHARACTER,
            source=user,
            target=character,
        )
        return character

    def get_corpus(self, character: Vertex) -> Vertex:
        return self.get_vertex_out_edges(vertex=character, type_name=EdgeType.HAS_CORPUS)[0].get_target()

    def get_mens(self, character: Vertex) -> Vertex:
        return self.get_vertex_out_edges(vertex=character, type_name=EdgeType.HAS_MENS)[0].get_target()

    def get_anima(self, character: Vertex) -> Vertex:
        return self.get_vertex_out_edges(vertex=character, type_name=EdgeType.HAS_ANIMA)[0].get_target()

    def get_personality(self, character: Vertex) -> Vertex:
        mens = self.get_mens(character)
        return self.get_vertex_out_edges(vertex=mens, type_name=EdgeType.HAS_PERSONALITY)[0].get_target()

    def get_attribute_value(self, node: Vertex) -> int:
        attribute = self.get_vertex_out_edges(vertex=node, type_name=EdgeType.HAS_ATTRIBUTE)[0].get_target()
        return attribute.get(name="value")

    def set_attribute_value(self, node: Vertex, value: int) -> None:
        attribute = self.get_vertex_out_edges(vertex=node, type_name=EdgeType.HAS_ATTRIBUTE)[0].get_target()
        self.update_vertex(attribute, value=value)
