from arcadedb_embedded.graph import Vertex
from database.repository.character import CharacterRepository
from database.store import WorldStore

class Character:
    def __init__(self, store: WorldStore, name: str, description: str, corpus_score: int, mens_score: int, anima_score: int) -> None:
        self.name: str = name
        self.description: str = description
        self.corpus_score: int = corpus_score
        self.mens_score: int = mens_score
        self.anima_score: int = anima_score
        
        self.character_repo: CharacterRepository = CharacterRepository(store.database)
        self.character: Vertex = self.character_repo.create_character(name=name, description=description)
        self.attributes: Vertex = self.character_repo.create_attributes(character=self.character)

    def set_corpus_score(self, score: int) -> None:
        self.character_repo.set_corpus_score(attributes=self.attributes, score=score)

    def set_mens_score(self, score: int) -> None:
        self.character_repo.set_mens_score(attributes=self.attributes, score=score)

    def set_anima_score(self, score: int) -> None:
        self.character_repo.set_anima_score(attributes=self.attributes, score=score)

    def get_corpus_score(self) -> int:
        return self.character_repo.get_corpus_score(attributes=self.attributes)

    def get_mens_score(self) -> int:
        return self.character_repo.get_mens_score(attributes=self.attributes)

    def get_anima_score(self) -> int:
        return self.character_repo.get_anima_score(attributes=self.attributes)