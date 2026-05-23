from datetime import datetime
from datetime import timezone
import uuid
from arcadedb_embedded.graph import Vertex
from core.model.database import VertexType, EdgeType
from database.repository.character import CharacterRepository


class CharacterService:
    def __init__(self, repo: CharacterRepository) -> None:
        self.repo = repo

    def create_character(
        self,
        name: str,
        description: str,
        corpus_score: int,
        mens_score: int,
        anima_score: int,
        extraversion: int,
        openness: int,
        neuroticism: int,
        agreeableness: int,
        conscientiousness: int,
    ) -> Vertex:
        character = self.repo.create_character(name=name, description=description)
        self._build_character_graph(
            character=character,
            corpus_score=corpus_score,
            mens_score=mens_score,
            anima_score=anima_score,
            extraversion=extraversion,
            openness=openness,
            neuroticism=neuroticism,
            agreeableness=agreeableness,
            conscientiousness=conscientiousness,
        )
        return character

    def _build_character_graph(
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
        self._scored_node(character, EdgeType.HAS_CORPUS, VertexType.CORPUS, corpus_score)
        mens = self._scored_node(character, EdgeType.HAS_MENS, VertexType.MENS, mens_score)
        self._scored_node(character, EdgeType.HAS_ANIMA, VertexType.ANIMA, anima_score)

        personality = self._container_node(mens, EdgeType.HAS_PERSONALITY, VertexType.PERSONALITY)

        ocean = [
            (EdgeType.HAS_EXTRAVERSION, VertexType.EXTRAVERSION, extraversion),
            (EdgeType.HAS_OPENNESS, VertexType.OPENNESS, openness),
            (EdgeType.HAS_NEUROTICISM, VertexType.NEUROTICISM, neuroticism),
            (EdgeType.HAS_AGREEABLENESS, VertexType.AGREEABLENESS, agreeableness),
            (EdgeType.HAS_CONSCIENTIOUSNESS, VertexType.CONSCIENTIOUSNESS, conscientiousness),
        ]
        for edge_type, vertex_type, value in ocean:
            self._scored_node(personality, edge_type, vertex_type, value)

    def _scored_node(
        self,
        parent: Vertex,
        edge_type: EdgeType,
        vertex_type: VertexType,
        value: int,
    ) -> Vertex:
        now = datetime.now(tz=timezone.utc)
        node = self.repo.create_vertex(
            type_name=vertex_type,
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
        )
        self.repo.create_edge(type_name=edge_type, source=parent, target=node, created_at=now, updated_at=now)
        attribute = self.repo.create_vertex(
            type_name=VertexType.ATTRIBUTE,
            id=str(uuid.uuid4()),
            value=value,
            created_at=now,
            updated_at=now,
        )
        self.repo.create_edge(type_name=EdgeType.HAS_ATTRIBUTE, source=node, target=attribute, created_at=now, updated_at=now)
        return node

    def _container_node(
        self,
        parent: Vertex,
        edge_type: EdgeType,
        vertex_type: VertexType,
    ) -> Vertex:
        now = datetime.now(tz=timezone.utc)
        node = self.repo.create_vertex(
            type_name=vertex_type,
            id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
        )
        self.repo.create_edge(type_name=edge_type, source=parent, target=node, created_at=now, updated_at=now)
        return node
