"""Procedural geology generation."""

from src.worldgen.geology.config import (
    CrustConfig,
    GeologyConfig,
    MagmaConfig,
    PlateConfig,
)
from src.worldgen.geology.generate import generate_geology
from src.worldgen.geology.model import CrustResult, GeologyResult

__all__ = [
    "CrustConfig",
    "CrustResult",
    "GeologyConfig",
    "GeologyResult",
    "MagmaConfig",
    "PlateConfig",
    "generate_geology",
]
