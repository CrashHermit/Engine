"""Biome stage: soft biome weights from climate via the one true BIOME_GRID.

Pipeline order: ``... → Leylines → Biomes``
"""

from src.worldgen.config.worldgen_config import BiomeConfig
from src.worldgen.context import WorldContext
from src.worldgen.ecology.biomes import (
    assign_biome_regions,
    biome_weights,
    derive_centers,
    smooth_biome_weights,
)
from src.worldgen.types import BoolArray, Float64Array, Int32Array


class BiomeStage:
    """Derive biome centers from ``BIOME_GRID`` and write IDW soft weights.

    Pipeline order: after Leylines (last ecology field the world needs).
    """

    def run(self, ctx: WorldContext) -> None:
        """Compute ``biome_weights`` and the ``region_id`` provinces it implies."""
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

        weights: Float64Array = biome_weights(
            temperature=temperature,
            precipitation=precipitation,
            is_land=biome_mask,
            center_temp=center_temp,
            center_precip=center_precip,
            cfg=cfg,
        )
        # Coherent regions instead of per-cell speckle (gradual ecotones).
        smoothed: Float64Array = smooth_biome_weights(
            geometry=ctx.geometry,
            weights=weights,
            biome_mask=biome_mask,
            cfg=cfg,
        )
        ctx.fields.biome_weights = smoothed

        # Provinces: connected same-biome regions with the small ones merged
        # away. The patchwork of per-cell biomes becomes a handful of coherent,
        # nameable regions (region_id); the soft weights above are untouched.
        region_id: Int32Array = assign_biome_regions(
            geometry=ctx.geometry,
            weights=smoothed,
            biome_mask=biome_mask,
            cfg=cfg,
        )
        ctx.fields.region_id = region_id
