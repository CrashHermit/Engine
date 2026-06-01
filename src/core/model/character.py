from dataclasses import dataclass


@dataclass
class CharacterData:
    id: str
    name: str
    description: str
    corpus: int
    mens: int
    anima: int
    extraversion: int
    openness: int
    agreeableness: int
    neuroticism: int
    conscientiousness: int
