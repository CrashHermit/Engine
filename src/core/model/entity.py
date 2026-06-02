from enum import StrEnum


class Danger(StrEnum):
    """An entity's structural threat ceiling (NPCs carry danger, not HP). Maps
    to a magnitude cap in threat_envelope.py. The structured entity DTO lives in
    core/model/location.py (EntityData)."""

    LOW = "low"
    STANDARD = "standard"
    ELITE = "elite"
    DEADLY = "deadly"


class EntityKind(StrEnum):
    """What an entity *is*. Only a CREATURE is a living foe — a valid attack
    target with a defeat clock that acts as an active threat source. An OBJECT
    is scenery: it may still threaten environmentally (rubble falls), but it
    cannot be 'defeated' and has no meaningful clock."""

    CREATURE = "creature"
    OBJECT = "object"

