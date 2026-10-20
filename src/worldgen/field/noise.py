"""Seeded OpenSimplex2S fields sampled at paired Cartesian XYZ coordinates."""

from dataclasses import dataclass

import numpy as np


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
    """Sample OpenSimplex2S fBm at paired Cartesian XYZ positions.

    Coordinates are passed through unchanged; the caller owns the coordinate
    frame. World generation uses normalized centered coordinates in ``[-1, 1]³``.
    """
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
    """Map the fixed octave-amplitude range to [0, 1], independent of samples."""
    values = fbm(
        positions,
        seed=seed,
        octaves=config.octaves,
        base_frequency=config.base_frequency,
        lacunarity=config.lacunarity,
        persistence=config.persistence,
    )
    amplitude_bound = sum(
        abs(config.persistence) ** octave for octave in range(config.octaves)
    )
    values = np.clip(0.5 + values / (2.0 * amplitude_bound), 0.0, 1.0)
    values.setflags(write=False)
    return values


def sample_vector_noise(
    positions: np.ndarray,
    config: NoiseConfig,
    *,
    seeds: tuple[int, int, int],
) -> np.ndarray:
    """Sample three independent signed noise channels at paired XYZ positions.

    Return an ``(N, 3)`` float64 array, with each channel mapped to ``[-1, 1]``.
    Coordinates are passed through unchanged; this function does not project or
    normalize them.
    """
    channels = (
        normalized_noise(positions, config, seed=seed) * 2.0 - 1.0 for seed in seeds
    )
    if len(positions) == 0:
        return np.empty((0, 3), dtype=np.float64)
    return np.column_stack(tuple(channels))


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
