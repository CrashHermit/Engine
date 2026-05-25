from arcadedb_embedded.graph import Vertex

from core.model.database import EdgeType, VertexType
from database.repository.character import CharacterRepository
from database.repository.location import LocationRepository
from database.repository.user import UserRepository


class CharacterService:
    def __init__(
        self,
        user_repo: UserRepository,
        character_repo: CharacterRepository,
        location_repo: LocationRepository,
    ) -> None:
        self._user_repo = user_repo
        self.character_repo = character_repo
        self.location_repo = location_repo

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
        with self.character_repo.transaction():
            character: Vertex = self.character_repo.create_character(
                user=user,
                name=name,
                description=description,
            )

            for vertex_type, edge_type, value in [
                (VertexType.CORPUS, EdgeType.HAS_CORPUS, corpus_score),
                (VertexType.MENS, EdgeType.HAS_MENS, mens_score),
                (VertexType.ANIMA, EdgeType.HAS_ANIMA, anima_score),
            ]:
                self.create_trait(
                    character=character,
                    vertex_type=vertex_type,
                    edge_type=edge_type,
                )
                self.create_attribute(
                    source=vertex_type,
                    value=value,
                )

            for vertex_type, edge_type, value in [
                (VertexType.EXTRAVERSION, EdgeType.HAS_EXTRAVERSION, extraversion),
                (VertexType.OPENNESS, EdgeType.HAS_OPENNESS, openness),
                (VertexType.NEUROTICISM, EdgeType.HAS_NEUROTICISM, neuroticism),
                (VertexType.AGREEABLENESS, EdgeType.HAS_AGREEABLENESS, agreeableness),
                (VertexType.CONSCIENTIOUSNESS, EdgeType.HAS_CONSCIENTIOUSNESS, conscientiousness),
            ]:
                self.create_trait(
                    character=character,
                    vertex_type=vertex_type,
                    edge_type=edge_type,
                )
                self.create_attribute(
                    source=vertex_type,
                    value=value,
                )

        return character

    def create_trait(self, character: Vertex, vertex_type: VertexType, edge_type: EdgeType) -> Vertex:
        trait: Vertex = self.character_repo.create_vertex(type_name=vertex_type)
        self.character_repo.create_edge(type_name=edge_type, source=character, target=trait)
        return trait

    def create_personality(
        self,
        character: Vertex,
        vertex_type: VertexType,
        edge_type: EdgeType,
    ) -> Vertex:
        personality: Vertex = self.character_repo.create_vertex(type_name=vertex_type)
        self.character_repo.create_edge(type_name=edge_type, source=character, target=personality)
        return personality

    def create_attribute(self, source: Vertex, value: int) -> Vertex:
        attribute: Vertex = self.character_repo.create_vertex(
            type_name=VertexType.ATTRIBUTE,
            value=value,
        )
        self.character_repo.create_edge(
            type_name=EdgeType.HAS_ATTRIBUTE,
            source=source,
            target=attribute,
        )
        return attribute
