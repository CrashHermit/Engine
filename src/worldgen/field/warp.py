"""Composable volumetric coordinate transforms for spatial fields."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


type ShearSampler = Callable[[np.ndarray, int, int, float], np.ndarray]


@dataclass(frozen=True, slots=True)
class ShearWarpConfig:
    iterations: int = 4
    amplitude: float = 0.24
    lacunarity: float = 1.7
    gain: float = 0.65


@dataclass(frozen=True, slots=True)
class ShearWarpField:
    """Compose independent scalar shears into an invertible 3D transform."""

    config: ShearWarpConfig
    shear: ShearSampler

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Map Cartesian coordinates into the sheared coordinate space."""
        return self._transform(positions, inverse=False)

    def inverse(self, positions: np.ndarray) -> np.ndarray:
        """Map sheared coordinates back into the original coordinate space."""
        return self._transform(positions, inverse=True)

    def _transform(self, positions: np.ndarray, *, inverse: bool) -> np.ndarray:
        transformed = np.array(positions, dtype=np.float64, copy=True)
        if (
            len(transformed) == 0
            or self.config.iterations == 0
            or self.config.amplitude == 0.0
        ):
            return transformed

        direction = -1.0 if inverse else 1.0
        iterations = (
            range(self.config.iterations - 1, -1, -1)
            if inverse
            else range(self.config.iterations)
        )
        axes = range(2, -1, -1) if inverse else range(3)
        for iteration in iterations:
            scale = self.config.amplitude * self.config.gain**iteration
            frequency_multiplier = self.config.lacunarity**iteration
            for axis in axes:
                plane_positions = np.delete(transformed, axis, axis=1)
                offsets = self.shear(
                    plane_positions, iteration, axis, frequency_multiplier
                )
                transformed[:, axis] += direction * scale * offsets
        return transformed
