"""Vulcanism stages: terrain + field before erosion, landmark volcanoes after.

Vulcanism splits across two pipeline points for a reason:

* :class:`VulcanismStage` runs **before erosion** (``... -> BoundaryUplift ->
  Vulcanism -> Erosion -> ...``).  It adds edifice height to ``uplift`` so the
  volcanic terrain is dissected and drained like everything else, writes the
  present-day ``volcanism`` field (which keeps the full submarine picture), and
  stashes the discrete-volcano *candidates* on the context.

* :class:`VolcanoesStage` runs **after finalize** (once ``is_land`` exists), and
  turns those candidates into discrete ``Volcano`` landmarks.  Doing this before
  the terrain was finished was the bug: the stage could not tell a breached
  island arc from a submarine one, so it stamped a volcano on every boundary
  cell.  With the land mask in hand it keeps the edifices that actually surfaced
  (plus one anchor per otherwise-submarine chain) and drops the rest.
"""

import numpy as np

from src.worldgen.config.worldgen_config import VulcanismConfig
from src.worldgen.context import WorldContext
from src.worldgen.features import Volcano, VolcanoKind, VolcanoStatus
from src.worldgen.terrain.boundaries import BoundaryFacts
from src.worldgen.terrain.plate_personalities import PlateProperties
from src.worldgen.terrain.vulcanism import (
    VolcanoSeed,
    compute_vulcanism,
    select_landmark_volcanoes,
)
from src.worldgen.types import BoolArray, Float64Array, Int32Array


class VulcanismStage:
    """Add volcanic uplift, write the volcanism field, stash volcano candidates."""

    def run(self, ctx: WorldContext) -> None:
        """Contribute edifice height and the volcanism field (pre-erosion)."""
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

        # Discrete volcanoes are materialised after finalize, when we know which
        # edifices breached (see VolcanoesStage).
        ctx.volcano_candidates = result.volcanoes


class VolcanoesStage:
    """Turn surfaced candidates into discrete ``Volcano`` landmarks (post-finalize)."""

    def run(self, ctx: WorldContext) -> None:
        """Select landmark volcanoes and write their fields and objects."""
        cfg: VulcanismConfig = ctx.config.vulcanism
        candidates: list[VolcanoSeed] = ctx.volcano_candidates or []

        is_land: BoolArray | None = ctx.fields.is_land
        if is_land is None:
            msg: str = "is_land must be set before VolcanoesStage"
            raise RuntimeError(msg)

        selected: list[VolcanoSeed] = select_landmark_volcanoes(
            geometry=ctx.geometry,
            candidates=candidates,
            is_land=is_land,
            cfg=cfg,
        )

        n: int = ctx.geometry.n_cells
        is_volcano: BoolArray = np.zeros(n, dtype=bool)
        volcano_id: Int32Array = np.full(n, -1, dtype=np.int32)
        volcanoes: list[Volcano] = []
        for new_id, seed in enumerate(selected):
            volcanoes.append(
                Volcano(
                    id=new_id,
                    cell=seed.cell,
                    kind=VolcanoKind(seed.kind),
                    status=VolcanoStatus(seed.status),
                    chain_id=seed.chain_id,
                    activity=seed.activity,
                    has_caldera=seed.has_caldera,
                )
            )
            is_volcano[seed.cell] = True
            volcano_id[seed.cell] = new_id

        ctx.fields.is_volcano = is_volcano
        ctx.fields.volcano_id = volcano_id
        ctx.volcanoes = volcanoes
