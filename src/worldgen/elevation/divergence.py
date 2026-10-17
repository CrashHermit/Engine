"""Continuous ridge, axial-valley, and shoulder profiles."""

import numpy as np

from src.worldgen.elevation.config import DivergenceConfig
from src.worldgen.elevation.profiles import divergent_profile


def divergence_value(
    distance: np.ndarray,
    config: DivergenceConfig,
    peak: np.ndarray,
    continental: np.ndarray,
) -> np.ndarray:
    """Evaluate signed material-specific divergent relief at finite-arc distances."""
    distance = np.asarray(distance, dtype=np.float64)
    peak = np.asarray(peak, dtype=np.float64)
    continental = np.asarray(continental, dtype=bool)
    profile = np.asarray(
        [
            divergent_profile(
                float(d),
                config.width_percent,
                bool(material),
                axial_width_fraction=config.axial_width_fraction,
                axial_depth_multiplier=config.axial_depth_multiplier,
                shoulder_height_multiplier=config.shoulder_height_multiplier,
            )
            if d < config.width_percent
            else 0.0
            for d, material in zip(distance, continental)
        ]
    )
    return profile * peak * config.height_percent
