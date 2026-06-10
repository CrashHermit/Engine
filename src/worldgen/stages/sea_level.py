from __future__ import annotations

from src.worldgen.config.worldgen_config import SeaLevelConfig
from src.worldgen.context import WorldContext


class SeaLevelStage:
    """Converts raw elevation values to ``is_land`` using a percentile cut.

    Finds the elevation at the ``(1 - target_land_fraction)`` percentile and
    uses it as sea level.  Cells at or above sea level become land.  All
    elevations are then remapped so that land is ``> 0`` and ocean ``< 0``.

    Pipeline position: after ``ElevationStage``, before ``ErosionStage``
    (or ``LandmassStage`` when erosion is disabled).
    """

    def __init__(self, config: SeaLevelConfig) -> None:
        self._config = config

    def run(self, ctx: WorldContext) -> WorldContext:
        cfg = self._config
        cells = ctx.data.mesh.cells

        sorted_heights = sorted(cell.env.terrain.z for cell in cells)
        target_idx = int((1.0 - cfg.target_land_fraction) * len(sorted_heights))
        target_idx = max(0, min(target_idx, len(sorted_heights) - 1))
        sea_level = sorted_heights[target_idx]

        scale = ctx.config.elevation.elevation_scale
        for cell in cells:
            terrain = cell.env.terrain
            terrain.is_land = terrain.z >= sea_level
            terrain.z = (terrain.z - sea_level) * scale

        return ctx
