"""Seeded OpenSimplex2S fields sampled through FastNoiseLite's public batch API."""

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
    """Sample OpenSimplex2S fBm at paired XYZ positions with isolated seed state."""
    from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, FractalType, NoiseType

    # FastNoiseLite seeds are signed 32-bit; world streams supply signed 64-bit.
    seed32 = (int(seed) + 2**31) % 2**32 - 2**31
    noise = FastNoiseLite(seed=seed32)
    noise.noise_type = NoiseType.NoiseType_OpenSimplex2S
    noise.fractal_type = FractalType.FractalType_None
    noise.frequency = 1.0
    values = np.zeros(len(positions), dtype=np.float64)
    amplitude = 1.0
    frequency = base_frequency
    for octave in range(octaves):
        shift = octave * 1123.456
        coords = np.asarray(
            (positions * frequency + shift).T, dtype=np.float32, order="C"
        )
        values += amplitude * noise.gen_from_coords(coords).astype(np.float64)
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
