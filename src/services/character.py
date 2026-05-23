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
        now = datetime.now(tz=timezone.utc)
        character = self.repo.create_character(name=name, description=description)

        corpus = self.repo.create_vertex(type_name=VertexType.CORPUS, id=str(uuid.uuid4()), created_at=now, updated_at=now)
        self.repo.create_edge(type_name=EdgeType.HAS_CORPUS, source=character, target=corpus, created_at=now, updated_at=now)
        self.repo.create_edge(type_name=EdgeType.HAS_ATTRIBUTE, source=corpus, target=self.repo.create_vertex(type_name=VertexType.ATTRIBUTE, id=str(uuid.uuid4()), value=corpus_score, created_at=now, updated_at=now), created_at=now, updated_at=now)

        mens = self.repo.create_vertex(type_name=VertexType.MENS, id=str(uuid.uuid4()), created_at=now, updated_at=now)
        self.repo.create_edge(type_name=EdgeType.HAS_MENS, source=character, target=mens, created_at=now, updated_at=now)
        self.repo.create_edge(type_name=EdgeType.HAS_ATTRIBUTE, source=mens, target=self.repo.create_vertex(type_name=VertexType.ATTRIBUTE, id=str(uuid.uuid4()), value=mens_score, created_at=now, updated_at=now), created_at=now, updated_at=now)

        anima = self.repo.create_vertex(type_name=VertexType.ANIMA, id=str(uuid.uuid4()), created_at=now, updated_at=now)
        self.repo.create_edge(type_name=EdgeType.HAS_ANIMA, source=character, target=anima, created_at=now, updated_at=now)
        self.repo.create_edge(type_name=EdgeType.HAS_ATTRIBUTE, source=anima, target=self.repo.create_vertex(type_name=VertexType.ATTRIBUTE, id=str(uuid.uuid4()), value=anima_score, created_at=now, updated_at=now), created_at=now, updated_at=now)

        personality = self.repo.create_vertex(type_name=VertexType.PERSONALITY, id=str(uuid.uuid4()), created_at=now, updated_at=now)
        self.repo.create_edge(type_name=EdgeType.HAS_PERSONALITY, source=mens, target=personality, created_at=now, updated_at=now)

        for edge_type, vertex_type, value in [
            (EdgeType.HAS_EXTRAVERSION, VertexType.EXTRAVERSION, extraversion),
            (EdgeType.HAS_OPENNESS, VertexType.OPENNESS, openness),
            (EdgeType.HAS_NEUROTICISM, VertexType.NEUROTICISM, neuroticism),
            (EdgeType.HAS_AGREEABLENESS, VertexType.AGREEABLENESS, agreeableness),
            (EdgeType.HAS_CONSCIENTIOUSNESS, VertexType.CONSCIENTIOUSNESS, conscientiousness),
        ]:
            trait = self.repo.create_vertex(type_name=vertex_type, id=str(uuid.uuid4()), created_at=now, updated_at=now)
            self.repo.create_edge(type_name=edge_type, source=personality, target=trait, created_at=now, updated_at=now)
            self.repo.create_edge(type_name=EdgeType.HAS_ATTRIBUTE, source=trait, target=self.repo.create_vertex(type_name=VertexType.ATTRIBUTE, id=str(uuid.uuid4()), value=value, created_at=now, updated_at=now), created_at=now, updated_at=now)

        return character
