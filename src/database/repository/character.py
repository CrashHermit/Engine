from datetime import datetime
from datetime import timezone
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
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        self.create_edge(
            type_name=EdgeType.HAS_CHARACTER,
            source=user,
            target=character,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )
        return character

    def build_character_graph(
        self,
        character: Vertex,
        corpus_score: int,
        mens_score: int,
        anima_score: int,
        extraversion: int,
        openness: int,
        neuroticism: int,
        agreeableness: int,
        conscientiousness: int,
    ) -> None:
        self._create_scored_node(character, EdgeType.HAS_CORPUS, VertexType.CORPUS, corpus_score)
        mens = self._create_scored_node(character, EdgeType.HAS_MENS, VertexType.MENS, mens_score)
        self._create_scored_node(character, EdgeType.HAS_ANIMA, VertexType.ANIMA, anima_score)

        personality = self._create_container_node(mens, EdgeType.HAS_PERSONALITY, VertexType.PERSONALITY)

        ocean = [
            (EdgeType.HAS_EXTRAVERSION, VertexType.EXTRAVERSION, extraversion),
            (EdgeType.HAS_OPENNESS, VertexType.OPENNESS, openness),
            (EdgeType.HAS_NEUROTICISM, VertexType.NEUROTICISM, neuroticism),
            (EdgeType.HAS_AGREEABLENESS, VertexType.AGREEABLENESS, agreeableness),
            (EdgeType.HAS_CONSCIENTIOUSNESS, VertexType.CONSCIENTIOUSNESS, conscientiousness),
        ]
        for edge_type, vertex_type, value in ocean:
            self._create_scored_node(personality, edge_type, vertex_type, value)

    def _create_scored_node(
        self,
        parent: Vertex,
        edge_type: EdgeType,
        vertex_type: VertexType,
        value: int,
    ) -> Vertex:
        now = datetime.now(tz=timezone.utc)
        node = self.create_vertex(
            type_name=vertex_type,
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
        )
        self.create_edge(
            type_name=edge_type,
            source=parent,
            target=node,
            created_at=now,
            updated_at=now,
        )
        attribute = self.create_vertex(
            type_name=VertexType.ATTRIBUTE,
            id=str(uuid.uuid4()),
            value=value,
            created_at=now,
            updated_at=now,
        )
        self.create_edge(
            type_name=EdgeType.HAS_ATTRIBUTE,
            source=node,
            target=attribute,
            created_at=now,
            updated_at=now,
        )
        return node

    def _create_container_node(
        self,
        parent: Vertex,
        edge_type: EdgeType,
        vertex_type: VertexType,
    ) -> Vertex:
        now = datetime.now(tz=timezone.utc)
        node = self.create_vertex(
            type_name=vertex_type,
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
        )
        self.create_edge(
            type_name=edge_type,
            source=parent,
            target=node,
            created_at=now,
            updated_at=now,
        )
        return node

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
        self.update_vertex(attribute, value=value, updated_at=datetime.now(tz=timezone.utc))
