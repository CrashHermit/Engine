"""Procedural geology generation."""

from src.worldgen.geology.config import (
    CrustConfig,
    CrustDensityConfig,
    GeologyConfig,
    HotspotConfig,
    PlateConfig,
    PlateMotionConfig,
    VolcanismConfig,
)
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.geology.generate import generate_geology
from src.worldgen.geology.motion import build_plate_motion_field
from src.worldgen.geology.model import (
    CrustResult,
    GeologyResult,
    HotspotResult,
    VolcanoSites,
    VolcanoSource,
    VolcanoState,
    VolcanismResult,
)

__all__ = [
    "CrustConfig",
    "CrustDensityConfig",
    "CrustResult",
    "GeologyConfig",
    "GeologyResult",
    "NoiseConfig",
    "PlateConfig",
    "PlateMotionConfig",
    "HotspotConfig",
    "HotspotResult",
    "VolcanismConfig",
    "VolcanismResult",
    "VolcanoSites",
    "VolcanoSource",
    "VolcanoState",
    "generate_geology",
    "build_plate_motion_field",
]
