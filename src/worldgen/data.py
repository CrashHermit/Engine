from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TileData:
    row: int
    col: int
    neighbors: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class EntityGen:
    name: str
    description: str
    scene_position: str
    kind: str = "object"  # "creature" | "object"
    danger: str = "standard"
    threat_channels: str = ""  # CSV, e.g. "corpus,mens"
    # Authored per-pillar clock capacities (pillar -> capacity). Empty = uniform
    # from danger; a pillar omitted from a non-empty profile is immune.
    pillar_profile: dict[str, int] = field(default_factory=dict)
    # Static aggro nature (predatory/territorial/guardian/skittish/neutral/friendly).
    disposition: str = "neutral"


@dataclass
class LocationGen:
    name: str
    description: str
    is_center: bool = False
    entities: list[EntityGen] = field(default_factory=list)


@dataclass
class DungeonData:
    # Locations and the adjacency pairs (indices into `locations`) that connect them.
    locations: list[LocationGen] = field(default_factory=list)
    connections: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class WorldData:
    name: str
    description: str
    size: int
    tiles: dict[tuple[int, int], TileData] = field(default_factory=dict)
    dungeon: DungeonData | None = None
