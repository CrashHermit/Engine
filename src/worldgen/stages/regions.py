"""Regions stage: segment the mesh into named geographic regions.

Pipeline order: last (``... → Biomes → Regions``).  Regions are a derived
labeling pass over the finished fields — placing it last lets future region
kinds consume any upstream field (biomes, savagery, ...) without reordering.
"""

from src.worldgen.context import WorldContext
from src.worldgen.regions.regions import assign_regions
from src.worldgen.types import BoolArray, Int32Array


class RegionsStage:
    """Write per-cell ``region_id`` and the ``Region`` list to the context."""

    def run(self, ctx: WorldContext) -> None:
        """Segment land/ocean bodies into named regions."""
        is_land_field: BoolArray | None = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before RegionsStage"
            raise RuntimeError(msg)

        landmass_field: Int32Array | None = ctx.fields.landmass_id
        if landmass_field is None:
            msg = "landmass_id must be set before RegionsStage"
            raise RuntimeError(msg)

        region_id, regions = assign_regions(
            geometry=ctx.geometry,
            is_land=is_land_field,
            landmass_id=landmass_field,
            seed=ctx.config.seed,
        )
        ctx.fields.region_id = region_id
        ctx.regions = regions
