"""Composite configuration for continuous tectonic partitions and motion."""

from dataclasses import dataclass, field

from src.worldgen.geology.motion import PlateMotionConfig


@dataclass(frozen=True, slots=True)
class PlateConfig:
    """Continuous tectonic partition and plate-motion settings."""

    plate_count: int = 32
    # Percentage of the unit reference length; the planet maps one unit to radius.
    transition_half_width_percent: float = 12.0
    motion: PlateMotionConfig = field(default_factory=PlateMotionConfig)
