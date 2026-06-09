from __future__ import annotations

from src.worldgen.config.worldgen_config import ElevationConfig
from src.worldgen.context import WorldContext
from src.worldgen.noise.field import DomainWarp
from src.worldgen.noise.sampler import FIELD_WARP_X, FIELD_WARP_Y
from src.worldgen.stages.elevation.layered_noise import LayeredNoiseProvider
from src.worldgen.stages.elevation.provider import ElevationProvider


def _build_provider(config: ElevationConfig, ctx: WorldContext) -> ElevationProvider:
    if config.provider == "anchors":
        from src.worldgen.stages.elevation.anchors import ContinentAnchorProvider

        return ContinentAnchorProvider(config, ctx.config.anchor, ctx)
    return LayeredNoiseProvider(config, ctx)


class ElevationStage:
    """Generates per-cell elevation on the Voronoi mesh.

    Pipeline:

    1. Build a pluggable ``ElevationProvider`` (macrostructure only).
    2. Domain-warp each cell's sample coordinate so coastlines are organic
       rather than following the provider's underlying geometry.
    3. Query the provider at the warped coordinate.
    4. Normalise to ``[0, 1]`` and apply the redistribution exponent.

    Pipeline position: after ``MeshStage``, before ``SeaLevelStage``.
    """

    def __init__(self, config: ElevationConfig) -> None:
        self._config: ElevationConfig = config

    def run(self, ctx: WorldContext) -> WorldContext:
        if ctx.data.mesh is None:
            return ctx

        cfg = self._config
        mesh = ctx.data.mesh
        provider = _build_provider(cfg, ctx)

        # Domain warp displacement is expressed as a fraction of world size so
        # warp_amplitude stays scale-independent (a small value in 0..1).
        span = min(mesh.width, mesh.height)
        warp = DomainWarp(
            ctx.sampler,
            field_id_x=FIELD_WARP_X,
            field_id_y=FIELD_WARP_Y,
            amplitude=cfg.warp_amplitude * span,
            frequency=cfg.warp_frequency,
        )

        raw: list[float] = []
        for cell in mesh.cells:
            wx, wy = warp.warp(cell.site[0], cell.site[1])
            raw.append(provider.elevation_at(wx, wy))

        raw_min = min(raw)
        raw_max = max(raw)
        span_val = (raw_max - raw_min) if raw_max != raw_min else 1.0

        for cell, value in zip(mesh.cells, raw):
            norm = (value - raw_min) / span_val
            cell.z = norm ** cfg.redistribution_power

        return ctx
