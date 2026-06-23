"""Vulcanism stage: arcs, hotspot chains, and ridges into terrain + volcanoes.

Pipeline order: ``... -> BoundaryUplift -> Vulcanism -> Erosion -> ...`` — before
erosion, so the volcanic edifices are dissected and drained like the rest of the
terrain.  Reads the shared ``ctx.boundary_facts``; writes the ``volcanism`` /
``is_volcano`` / ``volcano_id`` fields, adds edifice height to ``uplift``, and
sets ``ctx.volcanoes``.
"""

import numpy as np

from src.worldgen.config.worldgen_config import VulcanismConfig
from src.worldgen.context import WorldContext
from src.worldgen.features import Volcano, VolcanoKind, VolcanoStatus
from src.worldgen.terrain.boundaries import BoundaryFacts
from src.worldgen.terrain.plate_personalities import PlateProperties
from src.worldgen.terrain.vulcanism import compute_vulcanism
from src.worldgen.types import BoolArray, Float64Array, Int32Array


class VulcanismStage:
    """Build subduction arcs, hotspot trails, and ridges; mark volcanoes."""

    def run(self, ctx: WorldContext) -> None:
        """Add volcanic uplift and write the volcanism field + volcano objects."""
        cfg: VulcanismConfig = ctx.config.vulcanism

        facts: BoundaryFacts | None = ctx.boundary_facts
        if facts is None:
            msg: str = "boundary_facts must be set before VulcanismStage"
            raise RuntimeError(msg)
        plate_id: Int32Array | None = ctx.fields.plate_id
        if plate_id is None:
            msg = "plate_id must be set before VulcanismStage"
            raise RuntimeError(msg)
        properties: PlateProperties | None = ctx.plate_properties
        if properties is None:
            msg = "plate_properties must be set before VulcanismStage"
            raise RuntimeError(msg)
        uplift: Float64Array | None = ctx.fields.uplift
        if uplift is None:
            msg = "uplift must be set before VulcanismStage"
            raise RuntimeError(msg)

        result = compute_vulcanism(
            geometry=ctx.geometry,
            facts=facts,
            plate_id=plate_id,
            properties=properties,
            cfg=cfg,
            seed=ctx.seed_for("vulcanism"),
        )

        # Add edifice height; clamp so nothing goes negative.
        uplift += result.uplift_add
        np.maximum(uplift, 0.0, out=uplift)
        ctx.fields.volcanism = result.volcanism

        # Materialize discrete volcanoes and their per-cell lookup columns.
        n: int = ctx.geometry.n_cells
        is_volcano: BoolArray = np.zeros(n, dtype=bool)
        volcano_id: Int32Array = np.full(n, -1, dtype=np.int32)
        volcanoes: list[Volcano] = []
        for new_id, seed in enumerate(result.volcanoes):
            volcanoes.append(
                Volcano(
                    id=new_id,
                    cell=seed.cell,
                    kind=VolcanoKind(seed.kind),
                    status=VolcanoStatus(seed.status),
                    chain_id=seed.chain_id,
                    activity=seed.activity,
                    has_caldera=False,  # set in VP2
                )
            )
            is_volcano[seed.cell] = True
            volcano_id[seed.cell] = new_id

        ctx.fields.is_volcano = is_volcano
        ctx.fields.volcano_id = volcano_id
        ctx.volcanoes = volcanoes
