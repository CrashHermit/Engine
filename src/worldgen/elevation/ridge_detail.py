"""Continuous source-space crest structure, independent of geological motion."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import ScalarSample
from src.worldgen.field.noise import (
    NoiseConfig,
    normalized_noise,
    normalized_noise_with_gradient,
)
from src.worldgen.utilities.curves import smoothstep


@dataclass(frozen=True, slots=True)
class RidgeDetailConfig:
    """Collision crest blend and independent profile-specific detail strengths.

    Other responses use bounded modulation: arcs and shoulders vary without
    filling trenches or axial depressions. Fault modulation preserves signs.
    Set individual strengths to zero to restore their unmodulated profiles.
    """

    # Use distributed crests exclusively; broad collision uplift stays unchanged.
    blend: float = 1.0
    sharpness: float = 3.0
    # Bounded response modulation; zero restores each original profile.
    arc_strength: float = 0.45
    ridge_strength: float = 0.3
    rift_strength: float = 0.3
    transform_strength: float = 0.15
    shear_strength: float = 0.15
    noise: NoiseConfig = NoiseConfig(
        octaves=3, base_frequency=18.0, lacunarity=2.0, persistence=0.5
    )


@dataclass(frozen=True, slots=True)
class RidgeDetailField:
    noise_seed: int
    config: RidgeDetailConfig = RidgeDetailConfig()

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Return bounded crest weights at arbitrary Cartesian positions."""
        if len(positions) == 0:
            values = np.empty(0, dtype=np.float64)
        else:
            noise = normalized_noise(positions, self.config.noise, seed=self.noise_seed)
            values = (
                smoothstep(1.0 - np.abs(2.0 * noise - 1.0)) ** self.config.sharpness
            )
        values.setflags(write=False)
        return values

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Return bounded crest weights and their Cartesian gradients."""
        if len(positions) == 0:
            return ScalarSample(
                np.empty(0, dtype=np.float64), np.empty((0, 3), dtype=np.float64)
            )
        noise = normalized_noise_with_gradient(
            positions, self.config.noise, seed=self.noise_seed
        )
        transformed = 1.0 - np.abs(2.0 * noise.values - 1.0)
        values = smoothstep(transformed) ** self.config.sharpness
        inside = (transformed > 0.0) & (transformed < 1.0)
        smooth_derivative = 6.0 * transformed * (1.0 - transformed)
        sign = np.sign(2.0 * noise.values - 1.0)
        multiplier = (
            self.config.sharpness
            * np.power(smoothstep(transformed), self.config.sharpness - 1.0)
            * smooth_derivative
            * (-2.0 * sign)
        )
        multiplier[~inside] = 0.0
        gradients = multiplier[:, None] * noise.gradients
        return ScalarSample(values, gradients)
