from dataclasses import dataclass, field


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
    # Per-run survival economy (decisions #11-14). Stored as CHARACTER properties.
    stress: int = 0
    trauma: int = 0
    vices: list[str] = field(default_factory=list)
