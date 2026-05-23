from arcadedb_embedded.graph import Vertex
from database.repository.character import CharacterRepository
from database.store import WorldStore
from core.model.database import EdgeType, VertexType


class Character:
    def __init__(
        self,
        store: WorldStore,
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
    ) -> None:
        self.name = name
        self.description = description

        self.character_repo = CharacterRepository(store.database)
        self.character: Vertex = self.character_repo.create_character(name=name, description=description)
        self.character_repo.build_character_graph(
            character=self.character,
            corpus_score=corpus_score,
            mens_score=mens_score,
            anima_score=anima_score,
            extraversion=extraversion,
            openness=openness,
            neuroticism=neuroticism,
            agreeableness=agreeableness,
            conscientiousness=conscientiousness,
        )

    def get_corpus_score(self) -> int:
        return self.character_repo.get_attribute_value(self.character_repo.get_corpus(self.character))

    def get_mens_score(self) -> int:
        return self.character_repo.get_attribute_value(self.character_repo.get_mens(self.character))

    def get_anima_score(self) -> int:
        return self.character_repo.get_attribute_value(self.character_repo.get_anima(self.character))

    def set_corpus_score(self, value: int) -> None:
        self.character_repo.set_attribute_value(self.character_repo.get_corpus(self.character), value)

    def set_mens_score(self, value: int) -> None:
        self.character_repo.set_attribute_value(self.character_repo.get_mens(self.character), value)

    def set_anima_score(self, value: int) -> None:
        self.character_repo.set_attribute_value(self.character_repo.get_anima(self.character), value)

    def _get_ocean_node(self, edge_type: EdgeType) -> Vertex:
        personality = self.character_repo.get_personality(self.character)
        return self.character_repo.get_vertex_out_edges(vertex=personality, type_name=edge_type)[0].get_target()

    def get_extraversion(self) -> int:
        return self.character_repo.get_attribute_value(self._get_ocean_node(EdgeType.HAS_EXTRAVERSION))

    def get_openness(self) -> int:
        return self.character_repo.get_attribute_value(self._get_ocean_node(EdgeType.HAS_OPENNESS))

    def get_neuroticism(self) -> int:
        return self.character_repo.get_attribute_value(self._get_ocean_node(EdgeType.HAS_NEUROTICISM))

    def get_agreeableness(self) -> int:
        return self.character_repo.get_attribute_value(self._get_ocean_node(EdgeType.HAS_AGREEABLENESS))

    def get_conscientiousness(self) -> int:
        return self.character_repo.get_attribute_value(self._get_ocean_node(EdgeType.HAS_CONSCIENTIOUSNESS))

    def set_extraversion(self, value: int) -> None:
        self.character_repo.set_attribute_value(self._get_ocean_node(EdgeType.HAS_EXTRAVERSION), value)

    def set_openness(self, value: int) -> None:
        self.character_repo.set_attribute_value(self._get_ocean_node(EdgeType.HAS_OPENNESS), value)

    def set_neuroticism(self, value: int) -> None:
        self.character_repo.set_attribute_value(self._get_ocean_node(EdgeType.HAS_NEUROTICISM), value)

    def set_agreeableness(self, value: int) -> None:
        self.character_repo.set_attribute_value(self._get_ocean_node(EdgeType.HAS_AGREEABLENESS), value)

    def set_conscientiousness(self, value: int) -> None:
        self.character_repo.set_attribute_value(self._get_ocean_node(EdgeType.HAS_CONSCIENTIOUSNESS), value)
