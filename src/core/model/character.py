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
    # Per-run economy, persisted on the character (decision #11–13). Defaulted
    # so existing call sites that build a CharacterData need not change.
    stress: int = 0
    trauma: int = 0
