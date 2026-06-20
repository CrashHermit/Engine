from dataclasses import dataclass, field
from enum import StrEnum

from src.core.model.threat import Channel


class Danger(StrEnum):
    """An entity's structural threat ceiling (NPCs carry danger, not HP).

    Maps to a magnitude cap in threat_envelope.py.
    """

    LOW = "low"
    STANDARD = "standard"
    ELITE = "elite"
    DEADLY = "deadly"


class EntityKind(StrEnum):
    """Define what an entity *is* structurally.

    Only a CREATURE is a living foe — a valid attack target with a defeat clock
    that acts as an active threat source. An OBJECT is scenery: it may still
    threaten environmentally (rubble falls), but it cannot be 'defeated' and
    has no meaningful clock.
    """

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
    """Track a creature's standing in the scene.

    SUSPENDED creatures (a pillar broken, but not gone) stop generating
    threats; GONE creatures are removed.
    """

    ACTIVE: str = "active"
    SUSPENDED: str = "suspended"
    GONE: str = "gone"


class Disposition(StrEnum):
    """Describe a creature's static nature — how it tends to react to the player.

    Feeds the engagement check's escalation judgment. NEUTRAL/FRIENDLY never
    turn hostile on their own.
    """

    PREDATORY: str = "predatory"  # hunts; strikes when it notices prey
    TERRITORIAL: str = "territorial"  # attacks when its space is encroached
    GUARDIAN: str = "guardian"  # defends a charge/place; warns then strikes
    SKITTISH: str = "skittish"  # flees/avoids rather than fights
    NEUTRAL: str = "neutral"  # indifferent; won't initiate
    FRIENDLY: str = "friendly"  # well-disposed; won't initiate


class EntityStance(StrEnum):
    """Track a creature's current engagement posture toward the player.

    The aggro axis, orthogonal to EntityStatus. Only a HOSTILE creature
    generates threats. UNAWARE -> WARY -> HOSTILE is the escalation ladder.
    """

    UNAWARE: str = "unaware"  # hasn't noticed / dormant
    WARY: str = "wary"  # noticed, tense, not yet committed
    HOSTILE: str = "hostile"  # actively threatening


@dataclass
class EntityData:
    name: str
    description: str = ""
    scene_position: str = ""
    # Creature vs inert prop. Defaults to OBJECT so only entities explicitly
    # tagged as creatures are foes (can be targeted/defeated).
    kind: EntityKind = EntityKind.OBJECT
    # Structural spine fed to the threat classifier + magnitude cap. Defaulted
    # so existing call sites need not change.
    danger: Danger = Danger.STANDARD
    threat_channels: frozenset[Channel] = field(default_factory=frozenset)
    id: str = ""
    # Per-creature pillar profile (authored): pillar -> clock capacity. Empty =
    # unauthored (uniform from danger). A pillar omitted from a non-empty profile
    # is IMMUNE (can't be broken that way). Static config, not live state.
    pillar_profile: dict[ThreatPillar, int] = field(default_factory=dict)
    # De-threat resolution state. Each pillar the player attacks accrues its own
    # clock (filled segments); capacity comes from danger (Phase 1, uniform).
    # Filling a pillar breaks it: EXISTS -> GONE, others -> SUSPENDED.
    clocks: dict[ThreatPillar, int] = field(default_factory=dict)
    status: EntityStatus = EntityStatus.ACTIVE
    broken_pillar: ThreatPillar | None = None
    # When suspended: the fiction under which this creature re-engages (read by
    # the engagement check). Empty while active.
    returns_when: str = ""
    # Aggro axis (orthogonal to status): static nature + current posture. A
    # creature threatens only while HOSTILE; the engagement check escalates it.
    disposition: Disposition = Disposition.NEUTRAL
    stance: EntityStance = EntityStance.UNAWARE
