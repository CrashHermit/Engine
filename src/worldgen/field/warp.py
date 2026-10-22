"""Composable volumetric coordinate transforms for spatial fields."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


from src.worldgen.field.differential import VectorSample


type ShearGradientSampler = Callable[
    [np.ndarray, int, int, float], tuple[np.ndarray, np.ndarray]
]
type ShearSampler = Callable[[np.ndarray, int, int, float], np.ndarray]


@dataclass(frozen=True, slots=True)
class ShearWarpConfig:
    iterations: int = 4
    amplitude: float = 0.24
    lacunarity: float = 1.7
    gain: float = 0.65


@dataclass(frozen=True, slots=True)
class ShearWarpField:
    """Compose scalar shears with optional analytic plane-gradient callbacks.

    ``shear_with_gradient`` returns offsets with shape ``(N,)`` and gradients
    with shape ``(N, 2)``, ordered by the two input axes remaining after the
    sheared axis is removed.
    """

    config: ShearWarpConfig
    shear: ShearSampler
    shear_with_gradient: ShearGradientSampler | None = None

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Map Cartesian coordinates into the sheared coordinate space."""
        return self._transform(positions, inverse=False)

    def inverse(self, positions: np.ndarray) -> np.ndarray:
        """Map sheared coordinates back into the original coordinate space."""
        return self._transform(positions, inverse=True)

    def sample_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        """Map coordinates and return the exact derivative of the shear chain."""
        return self._transform_with_jacobian(positions, inverse=False)

    def inverse_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        """Invert coordinates and return the exact inverse-map Jacobian."""
        return self._transform_with_jacobian(positions, inverse=True)

    def _transform_with_jacobian(
        self, positions: np.ndarray, *, inverse: bool
    ) -> VectorSample:
        transformed = np.array(positions, dtype=np.float64, copy=True)
        jacobians = np.broadcast_to(np.eye(3), (len(transformed), 3, 3)).copy()
        if (
            len(transformed) == 0
            or self.config.iterations == 0
            or self.config.amplitude == 0.0
        ):
            return VectorSample(transformed, jacobians)
        direction = -1.0 if inverse else 1.0
        iterations = (
            range(self.config.iterations - 1, -1, -1)
            if inverse
            else range(self.config.iterations)
        )
        axes = range(2, -1, -1) if inverse else range(3)
        for iteration in iterations:
            scale = direction * self.config.amplitude * self.config.gain**iteration
            frequency_multiplier = self.config.lacunarity**iteration
            for axis in axes:
                plane_positions = np.delete(transformed, axis, axis=1)
                offsets, plane_gradients = self.shear_with_gradient(
                    plane_positions, iteration, axis, frequency_multiplier
                )
                other_axes = [index for index in range(3) if index != axis]
                local = np.broadcast_to(np.eye(3), (len(transformed), 3, 3)).copy()
                local[:, axis, other_axes] += scale * plane_gradients
                transformed[:, axis] += scale * offsets
                jacobians = np.einsum("nij,njk->nik", local, jacobians)
        return VectorSample(transformed, jacobians)

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
