"""Euclidean nearest-seed sampling in a shared Cartesian coordinate frame."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class VoronoiSample:
    """Categorical nearest-seed ownership at query positions."""

    owner_seed_id: np.ndarray


def sample_voronoi(positions: np.ndarray, seeds: np.ndarray) -> VoronoiSample:
    """Find the nearest seed for each paired ``(N, 3)`` XYZ query.

    Positions and seeds must use the same Cartesian coordinate frame. The
    sampler imposes no ``[0, 1]`` bounds; world generation uses centered
    normalized coordinates in ``[-1, 1]³``.

    Seed IDs refer to rows in the ``(S, 3)`` seed array. Equal-distance seeds
    are ordered by their row index.
    """
    query_points = np.asarray(positions, dtype=np.float64)
    seed_points = np.asarray(seeds, dtype=np.float64)
    differences = query_points[:, None, :] - seed_points[None, :, :]
    distances_squared = np.sum(differences**2, axis=2)
    owner_seed_id = np.argmin(distances_squared, axis=1)

    owner_seed_id.setflags(write=False)
    return VoronoiSample(owner_seed_id=owner_seed_id)


@dataclass(frozen=True, slots=True)
class VoronoiField3D:
    """A fixed seed cloud that can be sampled at successive XYZ positions."""

    seeds: np.ndarray

    def __post_init__(self) -> None:
        seeds = np.array(self.seeds, dtype=np.float64, copy=True)
        seeds.setflags(write=False)
        object.__setattr__(self, "seeds", seeds)

    def sample(self, positions: np.ndarray) -> VoronoiSample:
        """Return nearest-seed ownership for an ``(N, 3)`` query array."""
        return sample_voronoi(positions, self.seeds)
