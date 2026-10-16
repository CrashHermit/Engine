"""Seeded OpenSimplex scalar fields."""

import numpy as np


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
    return values
