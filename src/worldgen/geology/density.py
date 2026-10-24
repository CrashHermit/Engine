"""Continuous procedural crust-density anomaly in Cartesian source space."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import noise_multiplier, noise_multiplier_with_gradient


@dataclass(frozen=True, slots=True)
class CrustDensityConfig:
    """Relative procedural density-anomaly settings."""

    variation_strength: float = 0.2
    noise_frequency: float = 1.0


@dataclass(frozen=True, slots=True)
class CrustDensityField:
    config: CrustDensityConfig
    noise_seed: int

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Sample the relative density anomaly at source-space positions."""
        query_points = np.asarray(positions, dtype=np.float64)
        if len(query_points) == 0:
            values = np.empty(0, dtype=np.float64)
        else:
            values = (
                noise_multiplier(
                    query_points,
                    seed=self.noise_seed,
                    frequency=self.config.noise_frequency,
                    strength=self.config.variation_strength,
                )
                - 1.0
            )
        values.setflags(write=False)
        return values

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Sample the relative density anomaly and its analytic gradient."""
        sample = noise_multiplier_with_gradient(
            np.asarray(positions, dtype=np.float64),
            seed=self.noise_seed,
            frequency=self.config.noise_frequency,
            strength=self.config.variation_strength,
        )
        values = sample.values - 1.0
        values.setflags(write=False)
        return ScalarSample(values, sample.gradients)
