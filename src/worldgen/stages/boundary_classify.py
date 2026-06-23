"""Boundary classification stage: the single plate-border walk.

Runs once after plate personalities are assigned and stores ``BoundaryFacts`` on
the context.  ``BoundaryUpliftStage`` and (later) the vulcanism stage both read
``ctx.boundary_facts`` rather than re-deriving the convergence math.

Pipeline order: ``... -> PlatePersonality -> BoundaryClassify -> BoundaryUplift -> ...``
"""

from src.worldgen.context import WorldContext
from src.worldgen.terrain.boundaries import classify_boundaries
from src.worldgen.terrain.plate_personalities import PlateProperties
from src.worldgen.types import Int32Array


class BoundaryClassifyStage:
    """Walk plate borders once and write ``ctx.boundary_facts``."""

    def run(self, ctx: WorldContext) -> None:
        """Classify every plate boundary and store the per-cell facts."""
        plate_id_field: Int32Array | None = ctx.fields.plate_id
        if plate_id_field is None:
            msg: str = "plate_id must be set before BoundaryClassifyStage"
            raise RuntimeError(msg)

        properties: PlateProperties | None = ctx.plate_properties
        if properties is None:
            msg = "plate_properties must be set before BoundaryClassifyStage"
            raise RuntimeError(msg)

        ctx.boundary_facts = classify_boundaries(
            geometry=ctx.geometry,
            plate_id=plate_id_field,
            properties=properties,
        )
