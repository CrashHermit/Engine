"""Regions stage: segment the mesh into named geographic + biome regions.

Pipeline order: last (``... → Biomes → Regions``).  Regions are a derived
labeling pass over the finished fields — placing it last lets it consume the
biome weights (and future fields) without reordering.
"""

import numpy as np

from src.worldgen.context import WorldContext
from src.worldgen.ecology.biomes import derive_centers
from src.worldgen.regions.regions import assign_regions
from src.worldgen.types import BoolArray, Float64Array, Int32Array


class RegionsStage:
    """Write ``region_id`` / ``biome_region_id`` and the ``Region`` list."""

    def run(self, ctx: WorldContext) -> None:
        """Segment land/ocean bodies and biome-regions into named regions."""
        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before RegionsStage"
            raise RuntimeError(msg)

        is_lake_field: BoolArray | None = ctx.fields.is_lake
        if is_lake_field is None:
            msg = "is_lake must be set before RegionsStage"
            raise RuntimeError(msg)

        landmass_field: Int32Array | None = ctx.fields.landmass_id
        if landmass_field is None:
            msg = "landmass_id must be set before RegionsStage"
            raise RuntimeError(msg)

        weights_field: Float64Array | None = ctx.fields.biome_weights
        if weights_field is None:
            msg = "biome_weights must be set before RegionsStage"
            raise RuntimeError(msg)

        # Biome-regions live on dry land; their landscape is the dominant biome.
        biome_mask: BoolArray = is_land_field & ~is_lake_field
        dominant_biome: Int32Array = np.argmax(weights_field, axis=1).astype(np.int32)
        _center_temp, _center_precip, biome_order = derive_centers()

        region_id, biome_region_id, regions = assign_regions(
            geometry=ctx.geometry,
            is_land=is_land_field,
            landmass_id=landmass_field,
            biome_mask=biome_mask,
            dominant_biome=dominant_biome,
            biome_order=biome_order,
            seed=ctx.config.seed,
        )
        ctx.fields.region_id = region_id
        ctx.fields.biome_region_id = biome_region_id
        ctx.regions = regions
