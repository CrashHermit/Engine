import numpy as np

from src.worldgen.config.worldgen_config import TemperatureConfig
from src.worldgen.types import BoolArray, Float64Array


def compute_temperature(
    *,
    insolation: Float64Array,
    elevation: Float64Array,
    coast_distance: Float64Array,
    is_land: BoolArray,
    cfg: TemperatureConfig,
) -> Float64Array:
    """Compute temperature from insolation, lapse rate, and maritime moderation.

    Three effects applied in order:
    1. Base: temperature = insolation
    2. Lapse rate: cool elevation *above the lowland datum* (so a high-riding
       continental platform keeps its latitude's climate and only real mountains
       chill — measuring lapse from sea level would freeze raised interiors)
    3. Maritime moderation: coasts buffer toward sea temperature

    Args:
        insolation: Authored energy field in [0, 1].
        elevation: Normalized terrain height in [-1, 1]; 0 = sea level.
        coast_distance: Distance to nearest coast in hops.
        is_land: True for land cells, False for ocean.
        cfg: Temperature knobs (lapse rate, maritime reach/strength).

    Returns:
        Temperature in [0, 1], clamped.
    """
    temperature: Float64Array = insolation.copy()

    # --- lapse rate (mountains are cold) ---
    # Datum = a low percentile of land elevation (the lowland platform).  Only
    # relief above it cools, so a buoyant continent isn't uniformly frozen.
    land_elevation: Float64Array = np.maximum(0.0, elevation)
    datum: float = (
        float(np.percentile(land_elevation[is_land], cfg.lapse_datum_percentile))
        if np.any(is_land)
        else 0.0
    )
    temperature -= cfg.lapse_rate * np.maximum(0.0, land_elevation - datum)

    # --- maritime moderation (coasts are mild) ---
    maritime_weight: Float64Array = np.where(
        is_land,
        np.exp(-coast_distance / cfg.maritime_reach),
        1.0,
    )
    temperature += maritime_weight * cfg.maritime_strength * (
        insolation - temperature
    )

    # --- clamp to [0, 1] ---
    np.clip(temperature, 0.0, 1.0, out=temperature)

    return temperature
