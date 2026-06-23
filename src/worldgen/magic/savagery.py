"""Savagery: legible danger as a weighted blend of geography components.

Phase 4 step 1.  Savagery must be *legible* — a weighted blend of named,
normalized components (remoteness, harshness, ruggedness, noise), not raw
noise, so players can reason about why a place is dangerous.
"""

import numpy as np

from src.worldgen.config.worldgen_config import SavageryConfig
from src.worldgen.types import Float64Array


def compute_savagery(
    *,
    coast_distance: Float64Array,
    temperature: Float64Array,
    precipitation: Float64Array,
    slope: Float64Array,
    noise: Float64Array,
    volcanism: Float64Array,
    cfg: SavageryConfig,
) -> Float64Array:
    """Weighted blend of remoteness, harshness, ruggedness, and noise; clipped to [0, 1].

    Each component is normalized to ``[0, 1]`` before weighting:

    * **remoteness** — ``coast_distance`` over its own max (interiors are wild).
    * **harshness** — distance of ``(temperature, precipitation)`` from the
      comfort point, over its own max (frozen wastes and scorched deserts are
      savage; mild wet lands are tame).
    * **ruggedness** — ``slope`` over a high percentile (mountain country wild).
    * **noise** — one FBm field mapped to ``[0, 1]`` (nature isn't a formula).

    Args:
        coast_distance: Per-cell hop distance from the coast.
        temperature: Per-cell warmth in [0, 1].
        precipitation: Per-cell rainfall in [0, 1].
        slope: Per-cell steepest-descent gradient.
        noise: Per-cell FBm sample in roughly [-1, 1].
        cfg: Savagery weights and normalization knobs.

    Returns:
        savagery: Per-cell danger/wildness in [0, 1].
    """
    # --- remoteness: coast distance, max-normalized ---
    cd_max: float = float(coast_distance.max())
    remoteness: Float64Array = (
        coast_distance / cd_max if cd_max > 0.0 else np.zeros_like(coast_distance)
    )

    # --- harshness: climate distance from comfort, max-normalized ---
    d_temp: Float64Array = temperature - cfg.comfort_temperature
    d_precip: Float64Array = precipitation - cfg.comfort_precipitation
    harsh: Float64Array = np.sqrt(d_temp * d_temp + d_precip * d_precip)
    harsh_max: float = float(harsh.max())
    harshness: Float64Array = (
        harsh / harsh_max if harsh_max > 0.0 else np.zeros_like(harsh)
    )

    # --- ruggedness: slope, percentile-normalized ---
    slope_ref: float = float(np.percentile(a=slope, q=cfg.ruggedness_percentile))
    ruggedness: Float64Array = (
        np.clip(slope / slope_ref, 0.0, 1.0)
        if slope_ref > 0.0
        else np.zeros_like(slope)
    )

    # --- noise: map [-1, 1] FBm to [0, 1] ---
    noise01: Float64Array = (noise + 1.0) * 0.5

    savagery: Float64Array = (
        cfg.remoteness_weight * remoteness
        + cfg.harshness_weight * harshness
        + cfg.ruggedness_weight * ruggedness
        + cfg.noise_weight * noise01
        + cfg.volcanism_weight * volcanism  # live volcanic ground is dangerous
    )

    return np.clip(savagery, 0.0, 1.0)
