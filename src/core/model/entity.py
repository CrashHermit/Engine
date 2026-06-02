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


class ThreatPillar(StrEnum):
    """The conditions a creature needs to be a threat (Able + Engaged + Willing).
    Breaking any one neutralises it. The player's action targets one pillar; its
    clock tracks progress toward removing that condition.

    ABLE:     EXISTS (it is) · CAPABLE (it has the means)
    ENGAGED:  AWARE (it knows you) · IN_REACH (it can affect you)
    WILLING:  it wants to act
    """

    EXISTS = "exists"
    CAPABLE = "capable"
    AWARE = "aware"
    IN_REACH = "in_reach"
    WILLING = "willing"


class EntityStatus(StrEnum):
    """A creature's standing in the scene. SUSPENDED creatures (a pillar broken,
    but not gone) stop generating threats; GONE creatures are removed."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    GONE = "gone"


class Disposition(StrEnum):
    """A creature's static nature — how it tends to react to the player. Feeds
    the engagement check's escalation judgment. NEUTRAL/FRIENDLY never turn
    hostile on their own."""

    PREDATORY = "predatory"  # hunts; strikes when it notices prey
    TERRITORIAL = "territorial"  # attacks when its space is encroached
    GUARDIAN = "guardian"  # defends a charge/place; warns then strikes
    SKITTISH = "skittish"  # flees/avoids rather than fights
    NEUTRAL = "neutral"  # indifferent; won't initiate
    FRIENDLY = "friendly"  # well-disposed; won't initiate


class EntityStance(StrEnum):
    """A creature's current engagement posture toward the player (the aggro
    axis, orthogonal to EntityStatus). Only a HOSTILE creature generates
    threats. UNAWARE -> WARY -> HOSTILE is the escalation ladder."""

    UNAWARE = "unaware"  # hasn't noticed / dormant
    WARY = "wary"  # noticed, tense, not yet committed
    HOSTILE = "hostile"  # actively threatening

