"""Biome soft weights derived from the one true ``BIOME_GRID``.

Phase 4 step 6.  ``BIOME_GRID`` in ``core/model`` is the single source of
truth: worldgen *derives* each biome's ideal climate point from the band
breakpoints (bands are sevenths; band ``i`` midpoint ``(i + 0.5) / 7``) rather
than maintaining a separate ``biome_centers.py``.  Soft membership is then
inverse-distance weighting over those centers, done as one ``(n, n_biomes)``
matrix.
"""

import numpy as np

from src.core.model.environment.climate.precipitation import (
    ORDER as PRECIP_ORDER,
)
from src.core.model.environment.ecology.biome import BIOME_GRID, BiomeEnum
from src.core.model.environment.shared.temperature import ORDER as TEMP_ORDER
from src.worldgen.config.worldgen_config import BiomeConfig
from src.worldgen.types import BoolArray, Float64Array


def derive_centers() -> tuple[Float64Array, Float64Array, list[BiomeEnum]]:
    """Return ``(center_temp, center_precip, biome_order)`` from ``BIOME_GRID``.

    Each biome occupies one (temperature band × precipitation band) cell; its
    ideal point is that cell's midpoint.  ``biome_order`` is the single place
    the column index ↔ ``BiomeEnum`` mapping is defined: column
    ``t_idx * n_bands + p_idx``.

    Returns:
        center_temp: Ideal temperature per biome column, shape ``(n_biomes,)``.
        center_precip: Ideal precipitation per biome column.
        biome_order: ``BiomeEnum`` at each column index.
    """
    n_temp: int = len(TEMP_ORDER)
    n_precip: int = len(PRECIP_ORDER)

    center_temp: list[float] = []
    center_precip: list[float] = []
    biome_order: list[BiomeEnum] = []

    t_idx: int
    p_idx: int
    for t_idx, t_band in enumerate(TEMP_ORDER):
        for p_idx, p_band in enumerate(PRECIP_ORDER):
            center_temp.append((t_idx + 0.5) / n_temp)
            center_precip.append((p_idx + 0.5) / n_precip)
            biome_order.append(BIOME_GRID[(t_band, p_band)])

    return (
        np.array(center_temp, dtype=np.float64),
        np.array(center_precip, dtype=np.float64),
        biome_order,
    )


def biome_weights(
    *,
    temperature: Float64Array,
    precipitation: Float64Array,
    is_land: BoolArray,
    center_temp: Float64Array,
    center_precip: Float64Array,
    cfg: BiomeConfig,
) -> Float64Array:
    """Inverse-distance-weighted soft biome membership; shape ``(n, n_biomes)``.

    The broadcast ``T[:, None] - center_temp[None, :]`` *is* the nested
    cell × biome double loop, run in C.  Rows sum to 1 on cells where
    ``is_land`` is True (after the cutoff renormalize) and 0 elsewhere.

    Args:
        temperature: Per-cell warmth in [0, 1].
        precipitation: Per-cell rainfall in [0, 1].
        is_land: Mask of cells that should receive a biome distribution
            (ocean — and lake — cells are zeroed).
        center_temp: Ideal temperature per biome column.
        center_precip: Ideal precipitation per biome column.
        cfg: Biome IDW knobs (``blend_sharpness``, ``weight_cutoff``).

    Returns:
        weights: Soft biome distribution per cell, shape ``(n, n_biomes)``.
    """
    d2: Float64Array = (
        (temperature[:, None] - center_temp[None, :]) ** 2
        + (precipitation[:, None] - center_precip[None, :]) ** 2
    )  # (n, n_biomes)

    weights: Float64Array = 1.0 / (np.sqrt(d2) + 1e-3) ** cfg.blend_sharpness
    weights = weights / weights.sum(axis=1, keepdims=True)

    # Drop negligible weights, then renormalize so rows still sum to 1.
    weights = np.where(weights < cfg.weight_cutoff, 0.0, weights)
    row_sums: Float64Array = weights.sum(axis=1, keepdims=True)
    weights = np.divide(
        weights, row_sums, out=np.zeros_like(weights), where=row_sums > 0.0
    )

    # Ocean / lake cells have no biome.
    weights[~is_land] = 0.0

    return weights
