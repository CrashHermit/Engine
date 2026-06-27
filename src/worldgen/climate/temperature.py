import numpy as np

from src.worldgen.config.worldgen_config import TemperatureConfig
from src.worldgen.types import BoolArray, Float64Array
from src.worldgen.climate.ocean_current import maritime_sst_onshore
from src.worldgen.context import WorldContext


def compute_temperature(
    *,
    insolation: Float64Array,
    elevation: Float64Array,
    coast_distance: Float64Array,
    is_land: BoolArray,
    sst: Float64Array,
    maritime_sst: Float64Array,
    cfg: TemperatureConfig,
) -> Float64Array:
    """Compute temperature from insolation, lapse rate, and maritime moderation.

    Three effects applied in order:
    1. Base: temperature = insolation
    2. Lapse rate: cool elevation *above the lowland datum* (so a high-riding
       continental platform keeps its latitude's climate and only real mountains
       chill — measuring lapse from sea level would freeze raised interiors)
    3. Maritime moderation: coasts buffer toward the *real* sea-surface
       temperature carried onshore by the wind (``maritime_sst``), so a coast
       downwind of a warm current is mild and one downwind of cold upwelling is
       cold.  Ocean cells take their SST directly.

    Args:
        insolation: Authored energy field in [0, 1].
        elevation: Normalized terrain height in [-1, 1]; 0 = sea level.
        coast_distance: Distance to nearest coast in hops.
        is_land: True for land cells, False for ocean.
        sst: Sea-surface temperature in [0, 1] (ocean current; land = baseline).
        maritime_sst: Ocean SST carried onshore along the wind (the sea
            temperature a coast actually feels); equals ``sst`` over ocean.
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

    # --- maritime moderation (coasts buffer toward wind-borne sea temperature) ---
    maritime_weight: Float64Array = np.where(
        is_land,
        np.exp(-coast_distance / cfg.maritime_reach),
        1.0,
    )
    temperature += maritime_weight * cfg.maritime_strength * (
        maritime_sst - temperature
    )

    # --- ocean is its sea-surface temperature (the current is authoritative) ---
    temperature[~is_land] = sst[~is_land]

    # --- clamp to [0, 1] ---
    np.clip(temperature, 0.0, 1.0, out=temperature)

    return temperature


class TemperatureStage:
    """Compute temperature from insolation, elevation, and maritime effects.

    Pipeline order: ``Insolation → Wind → OceanCurrent → Temperature → Moisture``.
    Consumes the SST field from ``OceanCurrentStage``: ocean cells take their
    SST directly and coasts moderate toward the wind-borne ocean SST.
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute temperature and write ``ctx.fields.temperature``."""
        cfg: TemperatureConfig = ctx.config.temperature

        # --- prerequisites ---
        insolation_field: Float64Array | None = ctx.fields.insolation
        if insolation_field is None:
            msg: str = "insolation must be set before TemperatureStage"
            raise RuntimeError(msg)
        insolation: Float64Array = insolation_field

        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before TemperatureStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field

        coast_distance_field: Float64Array | None = ctx.fields.coast_distance
        if coast_distance_field is None:
            msg: str = "coast_distance must be set before TemperatureStage"
            raise RuntimeError(msg)
        coast_distance: Float64Array = coast_distance_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before TemperatureStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        sst_field: Float64Array | None = ctx.fields.sst
        if sst_field is None:
            msg = "sst must be set before TemperatureStage"
            raise RuntimeError(msg)
        sst: Float64Array = sst_field

        wind_u_field: Float64Array | None = ctx.fields.wind_u
        wind_v_field: Float64Array | None = ctx.fields.wind_v
        if wind_u_field is None or wind_v_field is None:
            msg = "wind must be set before TemperatureStage"
            raise RuntimeError(msg)

        # --- carry ocean SST onshore along the wind for maritime moderation ---
        maritime_sst: Float64Array = maritime_sst_onshore(
            geometry=ctx.geometry,
            wind_u=wind_u_field,
            wind_v=wind_v_field,
            sst=sst,
            insolation=insolation,
            is_land=is_land,
            reach=cfg.maritime_reach,
        )

        # --- compute ---
        ctx.fields.temperature = compute_temperature(
            insolation=insolation,
            elevation=elevation,
            coast_distance=coast_distance,
            is_land=is_land,
            sst=sst,
            maritime_sst=maritime_sst,
            cfg=cfg,
        )
