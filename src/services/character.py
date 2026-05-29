from arcadedb_embedded.graph import Vertex

from src.core.model.character import CharacterData
from src.core.model.database import EdgeType, VertexType
from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.repository.world import WorldRepository

# (VertexType, EdgeType) for the three top-level attribute categories.
_ATTRIBUTES = [
    (VertexType.CORPUS, EdgeType.HAS_CORPUS),
    (VertexType.MENS, EdgeType.HAS_MENS),
    (VertexType.ANIMA, EdgeType.HAS_ANIMA),
]

# (VertexType, EdgeType) for the big-five personality traits.
_TRAITS = [
    (VertexType.EXTRAVERSION, EdgeType.HAS_EXTRAVERSION),
    (VertexType.OPENNESS, EdgeType.HAS_OPENNESS),
    (VertexType.AGREEABLENESS, EdgeType.HAS_AGREEABLENESS),
    (VertexType.NEUROTICISM, EdgeType.HAS_NEUROTICISM),
    (VertexType.CONSCIENTIOUSNESS, EdgeType.HAS_CONSCIENTIOUSNESS),
]


class CharacterService:
    def __init__(
        self,
        base: BaseRepository,
        characters: CharacterRepository,
        worlds: WorldRepository,
    ) -> None:
        self._base = base
        self._characters = characters
        self._worlds = worlds

    ############################################################################
    # Reads
    ############################################################################

    def list_characters(self) -> list[CharacterData]:
        return [self._to_data(v) for v in self._characters.list_characters()]

    def get_character(self, character_id: str) -> CharacterData | None:
        vertex = self._characters.get_character(character_id)
        return self._to_data(vertex) if vertex is not None else None

    ############################################################################
    # Writes
    ############################################################################

    def create_character(
        self,
        name: str,
        description: str,
        corpus: int,
        mens: int,
        anima: int,
        extraversion: int,
        openness: int,
        agreeableness: int,
        neuroticism: int,
        conscientiousness: int,
        vice: str = "",
    ) -> CharacterData:
        attribute_values = {
            VertexType.CORPUS: corpus,
            VertexType.MENS: mens,
            VertexType.ANIMA: anima,
        }
        trait_values = {
            VertexType.EXTRAVERSION: extraversion,
            VertexType.OPENNESS: openness,
            VertexType.AGREEABLENESS: agreeableness,
            VertexType.NEUROTICISM: neuroticism,
            VertexType.CONSCIENTIOUSNESS: conscientiousness,
        }

        with self._base.transaction():
            character = self._characters.create_character(name=name, description=description)

            # Starting survival economy (decisions #11-14): a fresh track and the
            # one freeform starting vice.
            self._characters.set_economy(
                character,
                stress=0,
                trauma=0,
                vices=[vice] if vice else [],
            )

            for vertex_type, edge_type in _ATTRIBUTES:
                node = self._characters.add_node(character, vertex_type, edge_type)
                self._characters.add_attribute(node, attribute_values[vertex_type])

            mens_node = self._characters.get_mens(character)
            personality = self._characters.add_node(
                mens_node, VertexType.PERSONALITY, EdgeType.HAS_PERSONALITY
            )

            for vertex_type, edge_type in _TRAITS:
                node = self._characters.add_node(personality, vertex_type, edge_type)
                self._characters.add_attribute(node, trait_values[vertex_type])

            start_location = self._worlds.get_start_location()
            if start_location is not None:
                self._characters.place_character(character, start_location)

            return self._to_data(character)

    def delete_character(self, character_id: str) -> None:
        character = self._require(character_id)
        with self._base.transaction():
            self._characters.delete_character(character)

    ############################################################################
    # Internals
    ############################################################################

    def _require(self, character_id: str) -> Vertex:
        character = self._characters.get_character(character_id)
        if character is None:
            raise ValueError(f"Character not found: {character_id}")
        return character

    def _to_data(self, character: Vertex) -> CharacterData:
        personality = self._characters.get_personality(character)
        return CharacterData(
            id=character.get(name="id"),
            name=character.get(name="name") or "",
            description=character.get(name="description") or "",
            corpus=self._characters.get_attribute_value(self._characters.get_corpus(character)),
            mens=self._characters.get_attribute_value(self._characters.get_mens(character)),
            anima=self._characters.get_attribute_value(self._characters.get_anima(character)),
            extraversion=self._characters.get_trait_value(personality, EdgeType.HAS_EXTRAVERSION),
            openness=self._characters.get_trait_value(personality, EdgeType.HAS_OPENNESS),
            agreeableness=self._characters.get_trait_value(personality, EdgeType.HAS_AGREEABLENESS),
            neuroticism=self._characters.get_trait_value(personality, EdgeType.HAS_NEUROTICISM),
            conscientiousness=self._characters.get_trait_value(personality, EdgeType.HAS_CONSCIENTIOUSNESS),
            stress=self._characters.get_stress(character),
            trauma=self._characters.get_trauma(character),
            vices=self._characters.get_vices(character),
        )
