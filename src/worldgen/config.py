"""Top-level configuration for the current worldgen stages."""

from dataclasses import dataclass, field

from src.worldgen.geology.config import GeologyConfig


@dataclass(frozen=True, slots=True)
class WorldgenConfig:
    seed: int = 123
    subdivision_frequency: int = 20
    geology: GeologyConfig = field(default_factory=GeologyConfig)
