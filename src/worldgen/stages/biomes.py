"""Biome stage: soft biome weights from climate via the one true BIOME_GRID.

Pipeline order: ``... → Leylines → Biomes``
"""

from src.worldgen.config.worldgen_config import BiomeConfig
from src.worldgen.context import WorldContext
from src.worldgen.ecology.biomes import biome_weights, derive_centers
from src.worldgen.types import BoolArray, Float64Array


class BiomeStage:
    """Derive biome centers from ``BIOME_GRID`` and write IDW soft weights.

    Pipeline order: after Leylines (last ecology field the world needs).
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute ``biome_weights`` and write it to ``ctx.fields``."""
        cfg: BiomeConfig = ctx.config.biome

        # --- prerequisites ---
        temperature_field: Float64Array | None = ctx.fields.temperature
        if temperature_field is None:
            msg: str = "temperature must be set before BiomeStage"
            raise RuntimeError(msg)
        temperature: Float64Array = temperature_field

        precipitation_field: Float64Array | None = ctx.fields.precipitation
        if precipitation_field is None:
            msg = "precipitation must be set before BiomeStage"
            raise RuntimeError(msg)
        precipitation: Float64Array = precipitation_field

        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg = "is_land must be set before BiomeStage"
            raise RuntimeError(msg)
        is_land: BoolArray = is_land_field

        is_lake_field: BoolArray | None = ctx.fields.is_lake
        if is_lake_field is None:
            msg = "is_lake must be set before BiomeStage"
            raise RuntimeError(msg)
        is_lake: BoolArray = is_lake_field

        # Biomes live on dry land only; lake-covered cells carry no biome.
        biome_mask: BoolArray = is_land & ~is_lake

        center_temp, center_precip, _biome_order = derive_centers()

        ctx.fields.biome_weights = biome_weights(
            temperature=temperature,
            precipitation=precipitation,
            is_land=biome_mask,
            center_temp=center_temp,
            center_precip=center_precip,
            cfg=cfg,
        )
