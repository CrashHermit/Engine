from __future__ import annotations

from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.context import WorldContext
from src.worldgen.stages.base import Stage
from src.worldgen.stages.placeholder_elevation import PlaceholderElevationStage
from src.worldgen.stages.plate import PlatesStage
from src.worldgen.stages.plate_personality import PlatePersonalityStage
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.fields import MeshFields


def _build_stages() -> list[Stage]:
    """Return the ordered list of pipeline stages for the given config."""
    return [
        PlatesStage(),
        PlatePersonalityStage(),
        PlaceholderElevationStage(),
    ]


class WorldgenPipeline:
    """Phase 0 pipeline: mesh + placeholder elevation."""
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