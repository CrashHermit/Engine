"""Procedural geology generation."""

from src.worldgen.geology.config import (
    CrustConfig,
    CrustDensityConfig,
    GeologyConfig,
    MagmaConfig,
    PlateConfig,
)
from src.worldgen.geology.generate import generate_geology
from src.worldgen.geology.model import CrustResult, GeologyResult

__all__ = [
    "CrustConfig",
    "CrustDensityConfig",
    "CrustResult",
    "GeologyConfig",
    "GeologyResult",
    "MagmaConfig",
    "PlateConfig",
    "generate_geology",
]
