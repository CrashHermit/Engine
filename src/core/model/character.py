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
    # Display caps for the economy tracks, filled by the service from the
    # economy config. Carried on the DTO so the TUI can show "stress / max"
    # without importing core/mechanic (layer boundary — see code-style §2).
    stress_max: int = 0
    trauma_max: int = 0
