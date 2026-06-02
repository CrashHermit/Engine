from dataclasses import dataclass, field

from src.core.model.entity import Danger, EntityKind, EntityStatus, ThreatPillar
from src.core.model.threat import Channel


@dataclass
class EntityData:
    name: str
    description: str
    scene_position: str
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
    # the reengagement check). Empty while active.
    returns_when: str = ""


@dataclass
class LocationData:
    id: str
    name: str
    description: str


@dataclass
class LocationState:
    location: LocationData
    neighbors: list[LocationData] = field(default_factory=list)
    entities: list[EntityData] = field(default_factory=list)