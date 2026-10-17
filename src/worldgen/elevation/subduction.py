"""Continuous trench and overriding-plate arc profile evaluation."""

import numpy as np

from src.worldgen.elevation.config import SubductionConfig
from src.worldgen.elevation.profiles import subduction_profile


def subduction_value(
    signed_distance: np.ndarray,
    config: SubductionConfig,
    peak: np.ndarray,
    arc_variation: np.ndarray,
) -> np.ndarray:
    """Evaluate trench/arc relief from signed finite-arc distances."""
    values = np.asarray(
        [
            subduction_profile(
                float(distance),
                config.width_percent,
                trench_width_fraction=config.trench_width_fraction,
                arc_offset_fraction=config.arc_offset_fraction,
                arc_width_fraction=config.arc_width_fraction,
                arc_height_multiplier=config.arc_height_multiplier,
                arc_variation=float(variation),
            )
            if abs(distance) < config.width_percent
            else 0.0
            for distance, variation in zip(signed_distance, arc_variation)
        ]
    )
    return values * np.asarray(peak) * config.height_percent
