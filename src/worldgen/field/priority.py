"""Continuous noise and seed-distance priorities sampled on a sphere."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.field.noise import fbm


@dataclass(frozen=True, slots=True)
class PriorityFloodConfig:
    influence: float = 1.1
    octaves: int = 5
    base_frequency: float = 1.4
    lacunarity: float = 2.0
    persistence: float = 0.6


def noise_biased_priorities(
    positions: np.ndarray,
    seed_indices: np.ndarray,
    config: PriorityFloodConfig,
    *,
    noise_seed: int,
) -> np.ndarray:
    """Return spherical distance minus independent noise for each region."""
    priorities = np.empty((len(seed_indices), len(positions)), dtype=np.float64)
    for region, cell in enumerate(seed_indices):
        root = positions[cell]
        angle = np.arctan2(
            np.linalg.norm(np.cross(positions, root), axis=1), positions @ root
        )
        noise = fbm(
            positions,
            seed=noise_seed + 103 * region,
            octaves=config.octaves,
            base_frequency=config.base_frequency,
            lacunarity=config.lacunarity,
            persistence=config.persistence,
        )
        priorities[region] = angle - config.influence * noise
    return priorities
