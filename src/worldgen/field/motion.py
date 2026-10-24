"""Continuous Cartesian rigid-rotation fields."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.differential import VectorSample
from src.worldgen.field.voronoi import VoronoiField3D
from src.worldgen.geometry.rotation import (
    rotational_velocity,
    rotational_velocity_jacobian,
)


@dataclass(frozen=True, slots=True)
class RotationField:
    """Evaluate one global rigid rotation in Cartesian coordinates."""

    angular_velocity: np.ndarray

    def __post_init__(self) -> None:
        angular_velocity = np.array(self.angular_velocity, dtype=np.float64, copy=True)
        angular_velocity.setflags(write=False)
        object.__setattr__(self, "angular_velocity", angular_velocity)

    def sample(self, positions: np.ndarray) -> np.ndarray:
        """Return angular velocity crossed with each Cartesian position."""
        values = rotational_velocity(positions, self.angular_velocity)
        values.setflags(write=False)
        return values

    def sample_with_jacobian(self, positions: np.ndarray) -> VectorSample:
        """Return rotation velocities and their exact Cartesian Jacobian."""
        values = self.sample(positions)
        jacobians = np.broadcast_to(
            rotational_velocity_jacobian(self.angular_velocity),
            (len(values), 3, 3),
        )
        return VectorSample(values, jacobians)


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
        jacobians = rotational_velocity_jacobian(omegas)
        return VectorSample(values, jacobians)
