from __future__ import annotations

from src.worldgen.config.biome_centers import BIOME_CENTERS
from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.context import WorldContext
from src.worldgen.data import WorldData
from src.worldgen.stages.base import Stage
from src.worldgen.stages.biomes import BiomeStage
from src.worldgen.stages.climate import ClimateStage
from src.worldgen.stages.elevation.stage import ElevationStage
from src.worldgen.stages.erosion import ErosionStage
from src.worldgen.stages.grid import GridStage
from src.worldgen.stages.grid_derive import GridDeriveStage
from src.worldgen.stages.hydrology import HydrologyStage
from src.worldgen.stages.landmass import LandmassStage
from src.worldgen.stages.mesh import MeshStage
from src.worldgen.stages.river_rasterize import RiverRasterizeStage
from src.worldgen.stages.sea_level import SeaLevelStage


def _build_stages(config: WorldgenConfig) -> list[Stage]:
    """Return the ordered list of pipeline stages for the given config."""
    return [
        MeshStage(),
        ElevationStage(config.elevation),
        SeaLevelStage(config.sea_level),
        ErosionStage(config.erosion, config.sea_level),
        LandmassStage(config.landmass),
        HydrologyStage(config.hydrology),
        ClimateStage(config.climate),
        BiomeStage(BIOME_CENTERS, config.biome),
        GridStage(),
        GridDeriveStage(),
        RiverRasterizeStage(config.hydrology),
    ]


class WorldgenPipeline:
    """Runs the full worldgen pipeline and returns a populated ``WorldData``.

    Usage::

        from src.worldgen.data import WorldData
        from src.worldgen.pipeline import WorldgenPipeline

        world = WorldgenPipeline().run(WorldData(size=200, seed=42))

    Pass a ``WorldgenConfig`` to override defaults, or use one of the named
    presets from ``src.worldgen.config.presets``.
    """

    def __init__(self, config: WorldgenConfig | None = None) -> None:
        self._config: WorldgenConfig | None = config

    def run(self, world_data: WorldData) -> WorldData:
        ctx = WorldContext.build(world_data, self._config)
        for stage in _build_stages(ctx.config):
            ctx = stage.run(ctx)
        return ctx.data
