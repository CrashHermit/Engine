"""Cartesian axial coordinate fields."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import ScalarSample


@dataclass(frozen=True, slots=True)
class AxialCoordinateField:
    """Project Cartesian positions onto one normalized axial direction."""

    direction: np.ndarray

    def __post_init__(self) -> None:
        direction = np.array(self.direction, dtype=np.float64, copy=True)
        direction /= np.linalg.norm(direction)
        direction.setflags(write=False)
        object.__setattr__(self, "direction", direction)

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Return the linear axial coordinate for each Cartesian position."""
        points = np.asarray(positions, dtype=np.float64)
        values = np.einsum("ij,j->i", points, self.direction)
        values.setflags(write=False)
        return values

    def sample_with_gradient(self, positions: np.ndarray) -> ScalarSample:
        """Return axial coordinates and their constant Cartesian gradient."""
        points = np.asarray(positions, dtype=np.float64)
        values = np.einsum("ij,j->i", points, self.direction)
        gradients = np.broadcast_to(self.direction, points.shape).copy()
        return ScalarSample(values, gradients)
