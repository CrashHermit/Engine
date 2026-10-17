"""Continuous continental-collision profile evaluation."""

import numpy as np

from src.worldgen.elevation.config import CollisionConfig
from src.worldgen.elevation.profiles import collision_profile


def collision_value(
    distance: np.ndarray, config: CollisionConfig, peak: np.ndarray
) -> np.ndarray:
    """Evaluate broad collision relief and its narrow crest on exact arc distances."""
    distance = np.asarray(distance, dtype=np.float64)
    peak = np.asarray(peak, dtype=np.float64)
    out = np.zeros_like(distance)
    for index, (d, scale) in enumerate(zip(distance, peak)):
        if d < config.width_percent:
            broad, crest = collision_profile(
                float(d), config.width_percent, config.crest_width_fraction
            )
            out[index] = scale * (broad + config.crest_height_multiplier * crest)
    return out * config.height_percent
