from __future__ import annotations

from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.context import WorldContext
from src.worldgen.model import CellEnvironment, WorldData, WorldSpec
from src.worldgen.noise.sampler import FIELD_ALIGNMENT, FIELD_SAVAGERY
from src.worldgen.stages.base import Stage
from src.worldgen.stages.climate import ClimateStage
from src.worldgen.stages.elevation.stage import ElevationStage
from src.worldgen.stages.erosion import ErosionStage
from src.worldgen.stages.grid import GridStage
from src.worldgen.stages.grid_derive import GridDeriveStage
from src.worldgen.stages.hydrology import HydrologyStage
from src.worldgen.stages.landmass import LandmassStage
from src.worldgen.stages.mesh import MeshStage
from src.worldgen.stages.river_rasterize import RiverRasterizeStage
from src.worldgen.stages.scalar_field import (
    ScalarFieldStage,
    signed_field,
    unit_field,
)
from src.worldgen.stages.sea_level import SeaLevelStage


def _set_savagery(env: CellEnvironment, value: float) -> None:
    env.ecology.savagery = value


def _set_alignment(env: CellEnvironment, value: float) -> None:
    env.ecology.alignment = value


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
        ScalarFieldStage(
            config.savagery, FIELD_SAVAGERY, shape=unit_field, assign=_set_savagery
        ),
        ScalarFieldStage(
            config.alignment, FIELD_ALIGNMENT, shape=signed_field, assign=_set_alignment
        ),
        GridStage(),
        GridDeriveStage(),
        RiverRasterizeStage(config.hydrology),
    ]


class WorldgenPipeline:
    """Runs the full worldgen pipeline and returns a populated ``WorldData``.

    Usage::

        from src.worldgen.model import WorldSpec
        from src.worldgen.pipeline import WorldgenPipeline

        world = WorldgenPipeline().run(WorldSpec(size=200, seed=42))

    Pass a ``WorldgenConfig`` to override defaults, or use one of the named
    presets from ``src.worldgen.config.presets``.
    """

    def __init__(self, config: WorldgenConfig | None = None) -> None:
        self._config: WorldgenConfig | None = config

    def run(self, spec: WorldSpec) -> WorldData:
        ctx = WorldContext.build(spec, self._config)
        for stage in _build_stages(ctx.config):
            stage.run(ctx)
        return ctx.data
