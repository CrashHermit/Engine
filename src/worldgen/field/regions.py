"""Warped Voronoi partitions over centered Cartesian coordinates."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.noise import NoiseConfig
from src.worldgen.field.noise_warp import build_noise_shear_warp
from src.worldgen.field.seeds import generate_seed_cloud
from src.worldgen.field.voronoi import VoronoiField3D, VoronoiSample
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


@dataclass(frozen=True, slots=True)
class WarpedVoronoiField:
    """A volumetric warped Voronoi field sampled in centered world coordinates."""

    warp: ShearWarpField
    voronoi: VoronoiField3D

    def sample(self, positions: np.ndarray) -> VoronoiSample:
        """Sample region ownership at centered Cartesian ``(N, 3)`` positions."""
        return self.voronoi.sample(self.warp.sample(positions))


def build_warped_voronoi_field(
    seed_count: int,
    *,
    rng: np.random.Generator,
    noise_seed: int,
    noise_config: NoiseConfig = NoiseConfig(
        octaves=3, base_frequency=1.2, lacunarity=2.0, persistence=0.5
    ),
    warp_config: ShearWarpConfig = ShearWarpConfig(),
) -> WarpedVoronoiField:
    """Build a centered Cartesian warped Voronoi field from independent tools.

    Seed positions and query positions both use the centered world frame
    ``[-1, 1]³``. Queries pass directly through the volumetric warp and
    Voronoi field.
    """
    warp = build_noise_shear_warp(noise_config, warp_config, seed=noise_seed)
    voronoi = VoronoiField3D(generate_seed_cloud(seed_count, rng=rng))
    return WarpedVoronoiField(warp=warp, voronoi=voronoi)
