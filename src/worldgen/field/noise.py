"""Seeded OpenSimplex2S fields sampled at paired Cartesian XYZ coordinates."""

from dataclasses import dataclass

import numpy as np


from src.worldgen.field.differential import (
    ScalarHessianSample,
    ScalarSample,
    VectorSample,
)


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


def fbm_with_gradient(
    positions: np.ndarray,
    *,
    seed: int,
    octaves: int,
    base_frequency: float,
    lacunarity: float,
    persistence: float,
) -> ScalarSample:
    """Sample fBm and its Cartesian XYZ gradient at paired positions."""
    from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, FractalType, NoiseType

    seed32 = (int(seed) + 2**31) % 2**32 - 2**31
    noise = FastNoiseLite(seed=seed32)
    noise.noise_type = NoiseType.NoiseType_OpenSimplex2S
    noise.fractal_type = FractalType.FractalType_None
    noise.frequency = 1.0
    values = np.zeros(len(positions), dtype=np.float64)
    gradients = np.zeros((len(positions), 3), dtype=np.float64)
    amplitude = 1.0
    frequency = base_frequency
    for octave in range(octaves):
        shift = octave * 1123.456
        coords = np.asarray(
            (positions * frequency + shift).T, dtype=np.float32, order="C"
        )
        octave_values, octave_gradients = (
            noise.gen_open_simplex2s_with_gradient_from_coords(coords)
        )
        values += amplitude * octave_values.astype(np.float64)
        gradients += amplitude * frequency * octave_gradients.astype(np.float64)
        amplitude *= persistence
        frequency *= lacunarity
    values.setflags(write=False)
    gradients.setflags(write=False)
    return ScalarSample(values, gradients)


def fbm_with_hessian(
    positions: np.ndarray,
    *,
    seed: int,
    octaves: int,
    base_frequency: float,
    lacunarity: float,
    persistence: float,
) -> ScalarHessianSample:
    """Sample fBm and its analytic Cartesian XYZ gradient and Hessian."""
    from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, FractalType, NoiseType

    seed32 = (int(seed) + 2**31) % 2**32 - 2**31
    noise = FastNoiseLite(seed=seed32)
    noise.noise_type = NoiseType.NoiseType_OpenSimplex2S
    noise.fractal_type = FractalType.FractalType_None
    noise.frequency = 1.0
    values = np.zeros(len(positions), dtype=np.float64)
    gradients = np.zeros((len(positions), 3), dtype=np.float64)
    hessians = np.zeros((len(positions), 3, 3), dtype=np.float64)
    amplitude = 1.0
    frequency = base_frequency
    for octave in range(octaves):
        shift = octave * 1123.456
        coords = np.asarray(
            (positions * frequency + shift).T, dtype=np.float32, order="C"
        )
        octave_values, octave_gradients, octave_hessians = (
            noise.gen_open_simplex2s_with_hessian_from_coords(coords)
        )
        values += amplitude * octave_values.astype(np.float64)
        gradients += amplitude * frequency * octave_gradients.astype(np.float64)
        hessians += amplitude * frequency**2 * octave_hessians.astype(np.float64)
        amplitude *= persistence
        frequency *= lacunarity
    return ScalarHessianSample(values, gradients, hessians)


def normalized_noise_with_hessian(
    positions: np.ndarray, config: NoiseConfig, *, seed: int
) -> ScalarHessianSample:
    """Return fixed-range [0, 1] noise with analytic XYZ derivatives."""
    sample = fbm_with_hessian(
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
    unclipped = 0.5 + sample.values / (2.0 * amplitude_bound)
    values = np.clip(unclipped, 0.0, 1.0)
    gradients = sample.gradients / (2.0 * amplitude_bound)
    hessians = sample.hessians / (2.0 * amplitude_bound)
    clipped = (unclipped <= 0.0) | (unclipped >= 1.0)
    gradients[clipped] = 0.0
    hessians[clipped] = 0.0
    return ScalarHessianSample(values, gradients, hessians)


def normalized_noise_with_gradient(
    positions: np.ndarray, config: NoiseConfig, *, seed: int
) -> ScalarSample:
    """Return fixed-range [0, 1] noise and its analytic XYZ gradient."""
    sample = fbm_with_gradient(
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
    unclipped = 0.5 + sample.values / (2.0 * amplitude_bound)
    values = np.clip(unclipped, 0.0, 1.0)
    gradients = sample.gradients / (2.0 * amplitude_bound)
    gradients[(unclipped <= 0.0) | (unclipped >= 1.0)] = 0.0
    return ScalarSample(values, gradients)


def sample_vector_noise_with_jacobian(
    positions: np.ndarray, config: NoiseConfig, *, seeds: tuple[int, int, int]
) -> VectorSample:
    """Return signed independent noise channels and their Cartesian Jacobians."""
    channels = [
        normalized_noise_with_gradient(positions, config, seed=seed) for seed in seeds
    ]
    values = np.column_stack([2.0 * channel.values - 1.0 for channel in channels])
    jacobians = np.stack([2.0 * channel.gradients for channel in channels], axis=1)
    return VectorSample(values, jacobians)


def noise_multiplier_with_gradient(
    positions: np.ndarray, *, seed: int, frequency: float, strength: float
) -> ScalarSample:
    """Return a seeded noise multiplier and its analytic XYZ gradient."""
    sample = fbm_with_gradient(
        positions,
        seed=seed,
        octaves=1,
        base_frequency=frequency,
        lacunarity=2.0,
        persistence=0.5,
    )
    return ScalarSample(1.0 + strength * sample.values, strength * sample.gradients)


def noise_multiplier_with_hessian(
    positions: np.ndarray, *, seed: int, frequency: float, strength: float
) -> ScalarHessianSample:
    """Return a seeded noise multiplier and its analytic XYZ derivatives."""
    sample = fbm_with_hessian(
        positions,
        seed=seed,
        octaves=1,
        base_frequency=frequency,
        lacunarity=2.0,
        persistence=0.5,
    )
    return ScalarHessianSample(
        1.0 + strength * sample.values,
        strength * sample.gradients,
        strength * sample.hessians,
    )


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
