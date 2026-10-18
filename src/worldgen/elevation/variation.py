"""Continuous additive terrain-height variation on the unit sphere."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.config import TerrainVariationConfig
from src.worldgen.field.noise import normalized_noise


@dataclass(frozen=True, slots=True)
class TerrainVariationField:
    config: TerrainVariationConfig
    noise_seed: int

    def sample(self, positions: np.ndarray, radius_m: float) -> np.ndarray:
        """Return a zero-centered, radius-scaled terrain height contribution."""
        amplitude_m = self.config.amplitude_percent * (radius_m / 100.0)
        if amplitude_m == 0.0 or len(positions) == 0:
            return np.zeros(len(positions), dtype=np.float64)
        noise = normalized_noise(positions, self.config.noise, seed=self.noise_seed)
        return (2.0 * noise - 1.0) * amplitude_m
