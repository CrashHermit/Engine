"""Nexus aspects: mingling channels.

Phase 4 step 4.  Channel flavors mingle freely: each nexus gets three positive
weights over corpus/mens/anima, normalized, sharpened by an exponent so most
nexuses lean one channel without being pure.
"""

import random

import numpy as np

from src.worldgen.config.worldgen_config import LeylineConfig
from src.worldgen.types import Float64Array


def assign_aspects(
    *,
    nexus_cells: list[int],
    cfg: LeylineConfig,
    rng: random.Random,
) -> Float64Array:
    """Assign each nexus a sharpened channel mix.

    Args:
        nexus_cells: Mesh cell ids of the placed nexuses.
        cfg: Leyline configuration (channel purity exponent).
        rng: Seeded RNG for channel weights (the stage owns the seed).

    Returns:
        nexus_channels: Per-nexus channel weights, shape ``(k, 3)``.
    """
    k: int = len(nexus_cells)

    nexus_channels: Float64Array = np.zeros((k, 3), dtype=np.float64)

    idx: int
    for idx in range(k):
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

    return nexus_channels
