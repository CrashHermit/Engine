from __future__ import annotations

from src.worldgen.config.worldgen_config import PlatesConfig
from src.worldgen.context import WorldContext
from src.worldgen.terrain.plate_personalities import (
    PlateProperties,
    assign_plate_personalities,
    fill_uplift_from_plates,
)
from src.worldgen.types import Float64Array, Int32Array


class PlatePersonalityStage:
    """Assign continental/oceanic type, drift, and base uplift per plate."""

    def run(self, ctx: WorldContext) -> None:
        """Write ``uplift`` and store per-plate drift on the context."""
        cfg: PlatesConfig = ctx.config.plates
        plate_id_field: Int32Array | None = ctx.fields.plate_id
        if plate_id_field is None:
            msg: str = "plate_id must be set by PlatesStage before PlatePersonalityStage"
            raise RuntimeError(msg)
        plate_id: Int32Array = plate_id_field

        seed: int = ctx.seed_for(name="plate_personality")
        n_plates: int = cfg.n_plates

        properties: PlateProperties = assign_plate_personalities(
            n_plates=n_plates,
            seed=seed,
            config=cfg,
        )
        ctx.plate_properties: PlateProperties = properties
        ctx.fields.uplift: Float64Array = fill_uplift_from_plates(
            plate_id=plate_id,
            base_uplift=properties.base_uplift,
        )
