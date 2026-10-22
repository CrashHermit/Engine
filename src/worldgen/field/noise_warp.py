"""Compose scalar noise with the generic invertible shear transform."""

from dataclasses import replace

import numpy as np

from src.worldgen.field.noise import (
    NoiseConfig,
    normalized_noise,
    normalized_noise_with_gradient,
)
from src.worldgen.field.warp import ShearWarpConfig, ShearWarpField


def build_noise_shear_warp(
    noise_config: NoiseConfig,
    warp_config: ShearWarpConfig,
    *,
    seed: int,
) -> ShearWarpField:
    """Build an invertible shear transform from independent noise channels."""

    def sample_shear(
        plane_positions: np.ndarray,
        iteration: int,
        axis: int,
        frequency_multiplier: float,
    ) -> np.ndarray:
        noise_positions = np.insert(plane_positions, axis, 0.0, axis=1)
        iteration_config = replace(
            noise_config,
            base_frequency=noise_config.base_frequency * frequency_multiplier,
        )
        values = normalized_noise(
            noise_positions,
            iteration_config,
            seed=seed + 1013 * iteration + (11, 37, 71)[axis],
        )
        return 2.0 * values - 1.0

    def sample_shear_with_gradient(
        plane_positions: np.ndarray,
        iteration: int,
        axis: int,
        frequency_multiplier: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        noise_positions = np.insert(plane_positions, axis, 0.0, axis=1)
        iteration_config = replace(
            noise_config,
            base_frequency=noise_config.base_frequency * frequency_multiplier,
        )
        sample = normalized_noise_with_gradient(
            noise_positions,
            iteration_config,
            seed=seed + 1013 * iteration + (11, 37, 71)[axis],
        )
        gradient_axes = [index for index in range(3) if index != axis]
        return 2.0 * sample.values - 1.0, 2.0 * sample.gradients[:, gradient_axes]

    return ShearWarpField(
        config=warp_config,
        shear=sample_shear,
        shear_with_gradient=sample_shear_with_gradient,
    )
