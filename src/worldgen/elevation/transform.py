"""Continuous signed transform relief profiles."""

import numpy as np

from src.worldgen.elevation.config import TransformConfig
from src.worldgen.elevation.profiles import transform_profile


def transform_strength(normal: np.ndarray, shear: np.ndarray) -> np.ndarray:
    """Return signed normal/shear motion strength, with zero for a zero denominator."""
    denominator = np.abs(normal) + shear
    valid = denominator != 0.0
    strength = np.zeros_like(denominator, dtype=np.float64)
    strength[valid] = normal[valid] * shear[valid] / denominator[valid]
    return strength


def transform_value(
    distance: np.ndarray, config: TransformConfig, peak: np.ndarray
) -> np.ndarray:
    """Evaluate compact signed transform relief at exact boundary distances."""
    distance = np.asarray(distance, dtype=np.float64)
    peak = np.asarray(peak, dtype=np.float64)
    return (
        np.asarray(
            [
                transform_profile(float(value), config.width_percent)
                if value < config.width_percent
                else 0.0
                for value in distance
            ]
        )
        * peak
        * config.height_percent
    )
