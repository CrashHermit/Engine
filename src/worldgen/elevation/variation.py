"""Continuous additive terrain-height variation throughout 3D space."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.elevation.config import TerrainVariationConfig
from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import normalized_noise, normalized_noise_with_gradient


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

    def sample_fraction(self, positions: np.ndarray) -> np.ndarray:
        """Return the zero-centered variation as a fraction of planet radius."""
        values = self.sample(positions, radius_m=1.0)
        values.setflags(write=False)
        return values

    def sample_fraction_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Return radius-fraction terrain variation and its XYZ gradient."""
        query = np.asarray(positions, dtype=np.float64)
        if len(query) == 0 or self.config.amplitude_percent == 0.0:
            return ScalarSample(
                self.sample_fraction(query),
                np.zeros((len(query), 3), dtype=np.float64),
            )
        noise = normalized_noise_with_gradient(
            query, self.config.noise, seed=self.noise_seed
        )
        return ScalarSample(
            self.sample_fraction(query),
            (2.0 * self.config.amplitude_percent / 100.0) * noise.gradients,
        )
