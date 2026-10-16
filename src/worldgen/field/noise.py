"""Seeded OpenSimplex scalar fields."""

from dataclasses import dataclass

import numpy as np

from src.worldgen.utilities.normalize import interpolate_values


@dataclass(frozen=True, slots=True)
class NoiseConfig:
    octaves: int = 5
    base_frequency: float = 0.3
    lacunarity: float = 3.0
    persistence: float = 0.5


def fbm(
    positions: np.ndarray,
    *,
    seed: int,
    octaves: int,
    base_frequency: float,
    lacunarity: float,
    persistence: float,
) -> np.ndarray:
    """Sample OpenSimplex fractal Brownian motion at 3D positions."""
    from opensimplex.api import OpenSimplex

    noise = OpenSimplex(seed)
    values = np.zeros(len(positions), dtype=np.float64)
    amplitude = 1.0
    frequency = base_frequency
    for octave in range(octaves):
        shift = octave * 1123.456
        for index, position in enumerate(positions):
            values[index] += amplitude * noise.noise3(
                float(position[0] * frequency + shift),
                float(position[1] * frequency + shift),
                float(position[2] * frequency + shift),
            )
        amplitude *= persistence
        frequency *= lacunarity
    return values


def normalized_noise(
    positions: np.ndarray, config: NoiseConfig, *, seed: int
) -> np.ndarray:
    """Return the sampled noise remapped to [0, 1] and marked read-only."""
    values = interpolate_values(
        fbm(
            positions,
            seed=seed,
            octaves=config.octaves,
            base_frequency=config.base_frequency,
            lacunarity=config.lacunarity,
            persistence=config.persistence,
        ),
        (0.0, 1.0),
    )
    values.setflags(write=False)
    return values


def noise_multiplier(
    positions: np.ndarray,
    *,
    seed: int,
    frequency: float,
    strength: float,
) -> np.ndarray:
    """Return a seeded broad noise multiplier around one."""
    noise = fbm(
        positions,
        seed=seed,
        octaves=1,
        base_frequency=frequency,
        lacunarity=2.0,
        persistence=0.5,
    )
    return 1.0 + strength * noise
