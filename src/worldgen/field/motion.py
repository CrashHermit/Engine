"""Continuous rigid-rotation sampling for seed-indexed regions."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.regions import WarpedVoronoiField
from src.worldgen.geometry.rotation import rotational_velocity


@dataclass(frozen=True, slots=True)
class RegionRotationField:
    """Evaluate rigid rotation for a selected region at Cartesian positions."""

    regions: WarpedVoronoiField
    angular_velocity: np.ndarray

    def __post_init__(self) -> None:
        angular_velocity = np.array(self.angular_velocity, dtype=np.float64, copy=True)
        angular_velocity.setflags(write=False)
        object.__setattr__(self, "angular_velocity", angular_velocity)

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Sample the owning region's rotation at each original query position."""
        positions = np.asarray(positions, dtype=np.float64)
        owners = self.regions.sample(positions).owner_seed_id
        return self.sample_regions(positions, owners)

    def sample_regions(
        self, positions: np.ndarray, region_ids: np.ndarray
    ) -> np.ndarray:
        """Evaluate selected region rotations without querying ownership."""
        positions = np.asarray(positions, dtype=np.float64)
        region_ids = np.asarray(region_ids, dtype=np.int64)
        velocities = rotational_velocity(positions, self.angular_velocity[region_ids])
        velocities.setflags(write=False)
        return velocities
