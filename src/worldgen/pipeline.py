from __future__ import annotations

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.context import WorldContext
from src.worldgen.stages.base import Stage
from src.worldgen.stages.boundary_uplift import BoundaryUpliftStage
from src.worldgen.stages.erosion import ErosionStage
from src.worldgen.stages.finalize import FinalizeStage
from src.worldgen.stages.plate import PlatesStage
from src.worldgen.stages.plate_personality import PlatePersonalityStage
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.fields import MeshFields


def _build_stages() -> list[Stage]:
    """Return the ordered list of pipeline stages."""
    return [
        PlatesStage(),
        PlatePersonalityStage(),
        BoundaryUpliftStage(),
        ErosionStage(),
        FinalizeStage(),
    ]


class WorldgenPipeline:
    """Phase 1 pipeline: plates, boundary uplift, and erosion."""
    def __init__(self, config: WorldgenConfig | None = None) -> None:
        self._config: WorldgenConfig | None = config

    def run(self, seed: int, size: int) -> WorldContext:
        cfg: WorldgenConfig = WorldContext.resolve_config(seed=seed, size=size, config=self._config)
        mesh_cfg: MeshConfig = cfg.mesh

        geometry: MeshGeometry = build_mesh(
            seed=cfg.seed,
            cell_count=mesh_cfg.cell_count,
            lloyd_iterations=mesh_cfg.lloyd_iterations,
            width=mesh_cfg.width,
            height=mesh_cfg.height,
        )
        fields: MeshFields = MeshFields.allocate(n=geometry.n_cells)
        ctx: WorldContext = WorldContext(config=cfg, geometry=geometry, fields=fields)

        for stage in _build_stages():
            stage.run(ctx)

        return ctx