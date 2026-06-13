from __future__ import annotations

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.context import WorldContext
from src.worldgen.terrain.plates import build_plates


class PlatesStage:
    """Assign each mesh cell a tectonic plate id via ragged multi-source growth."""

    def run(self, ctx: WorldContext) -> None:
        """Write ``plate_id`` on the context fields from ``PlatesConfig``."""
        cfg: PlatesConfig = ctx.config.plates
        ctx.fields.plate_id = build_plates(
            geometry=ctx.geometry,
            n_plates=cfg.n_plates,
            seed=ctx.seed_for("plates"),
            growth_raggedness=cfg.growth_raggedness,
        )
