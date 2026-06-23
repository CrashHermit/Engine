"""Nexus aspects: clustered valence, mingling channels.

Phase 4 step 4.  Corrupt nexuses cluster (coherent blighted regions), while
channel flavors mingle freely.  Clustering needs no graph logic: sample a
*low-frequency* noise field at each nexus position — nearby nexuses sample
similar values — then sharpen toward the poles so most nexuses commit.
"""

import random

import numpy as np

from src.worldgen.config.worldgen_config import LeylineConfig
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.field import FractalField
from src.worldgen.types import Float64Array


def assign_aspects(
    *,
    geometry: MeshGeometry,
    nexus_cells: list[int],
    cfg: LeylineConfig,
    valence_noise: FractalField,
    rng: random.Random,
) -> tuple[Float64Array, Float64Array]:
    """Assign each nexus a clustered valence and a sharpened channel mix.

    Args:
        geometry: Torus mesh providing site positions.
        nexus_cells: Mesh cell ids of the placed nexuses.
        cfg: Leyline configuration (valence frequency, purity exponents).
        valence_noise: Low-frequency FBm field sampled at each nexus site.
        rng: Seeded RNG for channel weights (the stage owns the seed).

    Returns:
        nexus_valence: Per-nexus valence in [-1, 1], shape ``(k,)``.
        nexus_channels: Per-nexus channel weights, shape ``(k, 3)``.
    """
    k: int = len(nexus_cells)
    sites: Float64Array = geometry.sites

    nexus_valence: Float64Array = np.zeros(k, dtype=np.float64)
    nexus_channels: Float64Array = np.zeros((k, 3), dtype=np.float64)

    idx: int
    for idx in range(k):
        x: float = float(sites[nexus_cells[idx]][0])
        y: float = float(sites[nexus_cells[idx]][1])

        # Valence: low-frequency sample → spatial clustering for free.
        raw_v: float = valence_noise.sample(
            x=x, y=y, frequency=cfg.valence_frequency
        )
        # Sharpen toward the poles (-1 / +1), not toward 0.
        nexus_valence[idx] = float(
            np.sign(raw_v) * abs(raw_v) ** (1.0 / cfg.purity)
        )

        # Channels: 3 positive weights, normalized, sharpened, renormalized.
        weights: Float64Array = np.array(
            [rng.random(), rng.random(), rng.random()], dtype=np.float64
        )
        total: float = float(weights.sum())
        if total <= 0.0:
            weights = np.ones(3, dtype=np.float64)
            total = 3.0
        weights = weights / total
        weights = weights**cfg.channel_purity
        nexus_channels[idx] = weights / float(weights.sum())

    return nexus_valence, nexus_channels
