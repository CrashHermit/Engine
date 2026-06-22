"""Lakes stage: extract lakes as connected depressions, write is_lake and ctx.lakes.

Pipeline order: ``... → Rivers → Lakes → Flow``
"""


from src.worldgen.config.worldgen_config import LakeConfig
from src.worldgen.context import WorldContext
from src.worldgen.water.lakes import extract_lakes


class LakesStage:
    """Extract lakes and write is_lake / lake_id to fields.

    Phase 3 step 4: ``extract_lakes`` — BFS connected components on the
    lake mask ``is_land & (z_route > z + epsilon)``, outlet finding, and
    ``Lake`` object construction.

    Pipeline order: after RiversStage, before Flow stage.
    """

    def run(self, ctx: WorldContext) -> None:
        """Extract lakes and write is_lake, lake_id, and ctx.lakes."""
        n: int = ctx.geometry.n_cells
        cfg: LakeConfig = ctx.config.lake

        # --- prerequisites ---
        z_field = ctx.fields.z_route
        if z_field is None:
            msg: str = "z_route must be set before LakesStage"
            raise RuntimeError(msg)
        z_route = z_field

        elevation_field = ctx.fields.elevation
        if elevation_field is None:
            msg: str = "elevation must be set before LakesStage"
            raise RuntimeError(msg)
        elevation = elevation_field

        is_land_field = ctx.fields.is_land
        if is_land_field is None:
            msg: str = "is_land must be set before LakesStage"
            raise RuntimeError(msg)
        is_land = is_land_field

        # --- Extract lakes ---
        lakes, lake_id, is_lake = extract_lakes(
            geometry=ctx.geometry,
            z=elevation,
            z_route=z_route,
            is_land=is_land,
            cfg=cfg,
        )
        ctx.lakes = lakes

        # --- Write to fields ---
        ctx.fields.is_lake = is_lake
        ctx.fields.lake_id = lake_id
