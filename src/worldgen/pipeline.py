from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.context import WorldContext
from src.worldgen.stages.base import Stage
from src.worldgen.stages.boundary_uplift import BoundaryUpliftStage
from src.worldgen.stages.discharge import DischargeStage
from src.worldgen.stages.erosion import ErosionStage
from src.worldgen.stages.finalize import FinalizeStage
from src.worldgen.stages.plate import PlatesStage
from src.worldgen.stages.plate_personality import PlatePersonalityStage
from src.worldgen.stages.insolation import InsolationStage
from src.worldgen.stages.temperature import TemperatureStage
from src.worldgen.stages.wind import WindStage
from src.worldgen.stages.moisture import MoistureStage
from src.worldgen.stages.rivers import RiversStage
from src.worldgen.stages.lakes import LakesStage
from src.worldgen.stages.flow import FlowStage
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
        cfg: WorldgenConfig = WorldContext.resolve_config(
            seed=seed, size=size, config=self._config
        )
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

        # --- Phase 2: Climate ---
        self._run_climate(ctx)

        return ctx

    def _run_climate(self, ctx: WorldContext) -> None:
        """Run the climate stages after the terrain pipeline."""
        InsolationStage().run(ctx)
        TemperatureStage().run(ctx)
        WindStage().run(ctx)
        MoistureStage().run(ctx)

        # --- Phase 3: Water ---
        DischargeStage().run(ctx)
        RiversStage().run(ctx)
        LakesStage().run(ctx)
        FlowStage().run(ctx)
