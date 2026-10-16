"""Procedural geology generation."""

from src.worldgen.geology.config import (
    CrustConfig,
    CrustDensityConfig,
    GeologyConfig,
    HotspotConfig,
    PlateConfig,
)
from src.worldgen.field.noise import NoiseConfig
from src.worldgen.geology.generate import generate_geology
from src.worldgen.geology.model import CrustResult, GeologyResult, HotspotResult

__all__ = [
    "CrustConfig",
    "CrustDensityConfig",
    "CrustResult",
    "GeologyConfig",
    "GeologyResult",
    "NoiseConfig",
    "PlateConfig",
    "HotspotConfig",
    "HotspotResult",
    "generate_geology",
]
