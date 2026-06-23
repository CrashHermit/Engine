from src.worldgen.config.worldgen_config import LandmassConfig, SeaLevelConfig
from src.worldgen.context import WorldContext
from src.worldgen.terrain.finalize import (
    apply_sea_level,
    compute_coast_distance,
    compute_slope,
    label_landmasses,
    smooth_elevation,
)
from src.worldgen.types import BoolArray, Float64Array, Int32Array, Int8Array


class FinalizeStage:
    """Final elevation contract: sea level, normalisation, landmass labelling,
    coast distance, and slope.

    Pipeline order: ``... -> Erosion -> Finalize -> Bake -> Viewer``
    """

    def run(self, ctx: WorldContext) -> None:
        """Normalise elevation, label landmasses, and derive secondary fields.

        Args:
            ctx: Pipeline context with ``ctx.fields.elevation`` set by
                ``ErosionStage``.  Mutates ``ctx.fields`` in place.
        """
        n: int = ctx.geometry.n_cells
        sea_cfg: SeaLevelConfig = ctx.config.sea_level
        land_cfg: LandmassConfig = ctx.config.landmass

        # --- prerequisites ---
        elevation_field: Float64Array | None = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before FinalizeStage"
            raise RuntimeError(msg)
        elevation: Float64Array = elevation_field

        # --- 0. Coastal de-speckle (relax high-frequency wiggle pre-cut) ---
        elevation = smooth_elevation(
            elevation=elevation,
            geometry=ctx.geometry,
            passes=sea_cfg.coast_smoothing_passes,
            strength=sea_cfg.coast_smoothing_strength,
        )
        ctx.fields.elevation = elevation

        # --- 1. Sea level and piecewise normalisation ---
        is_land: BoolArray = apply_sea_level(
            elevation=elevation,
            target_land_fraction=sea_cfg.target_land_fraction,
        )
        ctx.fields.is_land = is_land

        # --- 2. Landmass labelling ---
        landmass_id: Int32Array
        landmass_class: Int8Array
        landmass_id, landmass_class = label_landmasses(
            is_land=is_land,
            geometry=ctx.geometry,
            n_cells=n,
            island_min_fraction=land_cfg.island_min_fraction,
            landmass_min_fraction=land_cfg.landmass_min_fraction,
        )
        ctx.fields.landmass_id = landmass_id
        ctx.fields.landmass_class = landmass_class

        # --- 3. Coast distance ---
        ctx.fields.coast_distance = compute_coast_distance(
            is_land=is_land,
            geometry=ctx.geometry,
            n_cells=n,
        )

        # --- 4. Slope ---
        ctx.fields.slope = compute_slope(
            elevation=elevation,
            geometry=ctx.geometry,
            n_cells=n,
        )
