class Character:
    def __init__(self, name: str, description: str, corpus_score: int, mens_score: int, anima_score: int) -> None:
        self.name: str = name
        self.description: str = description
        self.corpus_score: int = corpus_score
        self.mens_score: int = mens_score
        self.anima_score: int = anima_score