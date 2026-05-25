from arcadedb_embedded.graph import Vertex

from core.model.database import EdgeType, VertexType
from database.repository.base import BaseRepository
from database.repository.character import CharacterRepository
from database.repository.location import LocationRepository
from database.repository.user import UserRepository


class CharacterService:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base
        self._user_repo = UserRepository(base)
        self._character_repo = CharacterRepository(base)
        self._location_repo = LocationRepository(base)

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
        user = self._user_repo.get_or_create_user()
        with self._base.transaction():
            character: Vertex = self._character_repo.create_character(
                user=user,
                name=name,
                description=description,
            )

            for vertex_type, edge_type, value in [
                (VertexType.CORPUS, EdgeType.HAS_CORPUS, corpus_score),
                (VertexType.MENS, EdgeType.HAS_MENS, mens_score),
                (VertexType.ANIMA, EdgeType.HAS_ANIMA, anima_score),
            ]:
                trait = self._character_repo.create_trait(
                    character=character,
                    vertex_type=vertex_type,
                    edge_type=edge_type,
                )
                self._character_repo.create_attribute(source=trait, value=value)

            for vertex_type, edge_type, value in [
                (VertexType.EXTRAVERSION, EdgeType.HAS_EXTRAVERSION, extraversion),
                (VertexType.OPENNESS, EdgeType.HAS_OPENNESS, openness),
                (VertexType.NEUROTICISM, EdgeType.HAS_NEUROTICISM, neuroticism),
                (VertexType.AGREEABLENESS, EdgeType.HAS_AGREEABLENESS, agreeableness),
                (VertexType.CONSCIENTIOUSNESS, EdgeType.HAS_CONSCIENTIOUSNESS, conscientiousness),
            ]:
                trait = self._character_repo.create_trait(
                    character=character,
                    vertex_type=vertex_type,
                    edge_type=edge_type,
                )
                self._character_repo.create_attribute(source=trait, value=value)

        return character
