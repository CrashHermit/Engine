"""Continuous rigid-rotation sampling for seed-indexed regions."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.geometry.rotation import rotational_velocity
from src.worldgen.field.differential import VectorSample


@dataclass(frozen=True, slots=True)
class RegionRotationField:
    """Evaluate region rotations entirely in Cartesian source coordinates."""

    partition: VoronoiField3D
    angular_velocity: np.ndarray

    def __post_init__(self) -> None:
        angular_velocity = np.array(self.angular_velocity, dtype=np.float64, copy=True)
        angular_velocity.setflags(write=False)
        object.__setattr__(self, "angular_velocity", angular_velocity)

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Use source-space ownership and velocity at the same source position."""
        positions = np.asarray(positions, dtype=np.float64)
        owners = self.partition.sample(positions).owner_seed_id
        return self.sample_regions(positions, owners)

    def sample_regions(
        self, positions: np.ndarray, region_ids: np.ndarray
    ) -> np.ndarray:
        """Evaluate explicit region rotations at Cartesian source positions."""
        positions = np.asarray(positions, dtype=np.float64)
        region_ids = np.asarray(region_ids, dtype=np.int64)
        velocities = rotational_velocity(positions, self.angular_velocity[region_ids])
        velocities.setflags(write=False)
        return velocities

    def sample_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        """Sample ownership-selected velocities and their piecewise Jacobians."""
        query_points = np.asarray(positions, dtype=np.float64)
        owners = self.partition.sample(query_points).owner_seed_id
        return self.sample_regions_with_jacobian(query_points, owners)

    def sample_regions_with_jacobian(
        self, positions: np.ndarray, region_ids: np.ndarray
    ) -> VectorSample:
        """Evaluate explicit region velocities and Euler Jacobians."""
        points = np.asarray(positions, dtype=np.float64)
        ids = np.asarray(region_ids, dtype=np.int64)
        omegas = self.angular_velocity[ids]
        values = np.cross(omegas, points)
        jacobians = np.zeros((len(points), 3, 3), dtype=np.float64)
        jacobians[:, 0, 1] = -omegas[:, 2]
        jacobians[:, 0, 2] = omegas[:, 1]
        jacobians[:, 1, 0] = omegas[:, 2]
        jacobians[:, 1, 2] = -omegas[:, 0]
        jacobians[:, 2, 0] = -omegas[:, 1]
        jacobians[:, 2, 1] = omegas[:, 0]
        return VectorSample(values, jacobians)
