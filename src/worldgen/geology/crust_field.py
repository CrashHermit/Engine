"""Categorical crust ownership in shared Cartesian source space."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.seeds import generate_seed_cloud
from src.worldgen.field.voronoi import VoronoiField3D


@dataclass(frozen=True, slots=True)
class CrustPartitionConfig:
    """Independent continuous crust partition seed counts and transition width."""

    continental_seeds: int = 6
    oceanic_seeds: int = 18
    # Material blend spans remain dimensionless; this is a spatial overlap width.
    transition_half_width_percent: float = 12.0


@dataclass(frozen=True, slots=True)
class CrustSample:
    region_ids: np.ndarray
    continental: np.ndarray


@dataclass(frozen=True, slots=True)
class CrustField:
    """Categorical ownership; outer compositions supply shared coordinate warps."""

    partition: VoronoiField3D
    continental_regions: np.ndarray

    def __post_init__(self) -> None:
        labels = np.array(self.continental_regions, dtype=bool, copy=True)
        labels.setflags(write=False)
        object.__setattr__(self, "continental_regions", labels)

    def sample(self, positions: np.ndarray) -> CrustSample:
        """Return categorical crust ownership and its material label."""
        region_ids = self.partition.sample(positions).owner_seed_id
        continental = self.continental_regions[region_ids]
        continental.setflags(write=False)
        return CrustSample(region_ids, continental)


def build_crust_field(
    config: CrustPartitionConfig, *, rng: np.random.Generator
) -> CrustField:
    """Generate an independent seed cloud and randomly assign material labels.

    Counts specify starting regions, not continental surface-area fractions.
    No warp or random global state is created here.
    """
    count = config.continental_seeds + config.oceanic_seeds
    partition = VoronoiField3D(generate_seed_cloud(count, rng=rng))
    continental = np.zeros(count, dtype=bool)
    continental[rng.permutation(count)[: config.continental_seeds]] = True
    return CrustField(partition, continental)
