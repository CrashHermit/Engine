import numpy as np

from src.worldgen.bake.grid import bake_and_stamp, nearest_cell_per_tile
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.context import WorldContext
from src.worldgen.features import Landmass, LeylineNetwork, WorldData
from src.worldgen.fields import GridFields, MeshFields
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.stages.base import Stage
from src.worldgen.stages.biomes import BiomeStage
from src.worldgen.stages.boundary_classify import BoundaryClassifyStage
from src.worldgen.stages.boundary_uplift import BoundaryUpliftStage
from src.worldgen.stages.discharge import DischargeStage
from src.worldgen.stages.erosion import ErosionStage
from src.worldgen.stages.finalize import FinalizeStage
from src.worldgen.stages.flow import FlowStage
from src.worldgen.stages.insolation import InsolationStage
from src.worldgen.stages.lakes import LakesStage
from src.worldgen.stages.leylines import LeylinesStage
from src.worldgen.stages.moisture import MoistureStage
from src.worldgen.stages.ocean_current import OceanCurrentStage
from src.worldgen.stages.plate import PlatesStage
from src.worldgen.stages.plate_personality import PlatePersonalityStage
from src.worldgen.stages.rivers import RiversStage
from src.worldgen.stages.savagery import SavageryStage
from src.worldgen.stages.temperature import TemperatureStage
from src.worldgen.stages.vulcanism import VolcanoesStage, VulcanismStage
from src.worldgen.stages.wind import WindStage
from src.worldgen.types import Int32Array


def _build_stages() -> list[Stage]:
    """Return the ordered list of pipeline stages (Phases 1–4)."""
    return [
        # Phase 1 — terrain
        PlatesStage(),
        PlatePersonalityStage(),
        BoundaryClassifyStage(),
        BoundaryUpliftStage(),
        VulcanismStage(),
        ErosionStage(),
        FinalizeStage(),
        VolcanoesStage(),  # discrete volcanoes once we know which edifices breached
        # Phase 2 — climate
        # Wind precedes OceanCurrent + Temperature: SST is wind-advected, and
        # coasts moderate toward the wind-borne sea-surface temperature.
        InsolationStage(),
        WindStage(),
        OceanCurrentStage(),
        TemperatureStage(),
        MoistureStage(),
        # Phase 3 — water
        DischargeStage(),
        RiversStage(),
        LakesStage(),
        FlowStage(),
        # Phase 4 — magic & ecology
        SavageryStage(),
        LeylinesStage(),
        BiomeStage(),
    ]


def _build_landmasses(ctx: WorldContext, grid: GridFields) -> list[Landmass]:
    """Summarize the connected land components for the output contract."""
    mesh_ids: Int32Array = ctx.fields.landmass_id
    mesh_class = ctx.fields.landmass_class
    grid_ids: Int32Array = grid.landmass_id
    if mesh_ids is None or mesh_class is None or grid_ids is None:
        msg: str = "landmass fields must be set before assembling WorldData"
        raise RuntimeError(msg)

    landmasses: list[Landmass] = []
    max_id: int = int(mesh_ids.max()) if mesh_ids.size else 0
    component: int
    for component in range(1, max_id + 1):
        member: Int32Array = mesh_ids == component
        cell_count: int = int(np.count_nonzero(member))
        if cell_count == 0:
            continue
        landmasses.append(
            Landmass(
                id=component,
                cell_count=cell_count,
                tile_count=int(np.count_nonzero(grid_ids == component)),
                landmass_class=int(mesh_class[member][0]),
            )
        )
    return landmasses


class WorldgenPipeline:
    """Full worldgen pipeline: terrain, climate, water, magic, and assembly.

    ``run`` returns the product ``WorldData`` (the mesh is an internal
    intermediate that does not ship).  ``run_debug`` additionally returns the
    ``WorldContext`` for the viewer, which needs mesh-side intermediates.
    """

    def __init__(self, config: WorldgenConfig | None = None) -> None:
        self._config: WorldgenConfig | None = config

    def run(self, seed: int, size: int) -> WorldData:
        """Generate a world and return the product ``WorldData``."""
        world, _ctx = self.run_debug(seed=seed, size=size)
        return world

    def run_debug(
        self, seed: int, size: int
    ) -> tuple[WorldData, WorldContext]:
        """Generate a world and return ``(WorldData, WorldContext)`` for debug.

        The viewer uses this door for mesh-side intermediates; the product
        ``run`` entry point throws the context (and its mesh) away.
        """
        ctx: WorldContext = self._run_pipeline(seed=seed, size=size)
        world: WorldData = self._assemble(ctx)
        return world, ctx

    def _run_pipeline(self, seed: int, size: int) -> WorldContext:
        """Build the mesh and run every stage; return the populated context."""
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
        ctx: WorldContext = WorldContext(
            config=cfg, geometry=geometry, fields=fields
        )

        for stage in _build_stages():
            stage.run(ctx)

        return ctx

    def _assemble(self, ctx: WorldContext) -> WorldData:
        """Bake the grid, stamp rivers, and assemble the output ``WorldData``."""
        size: int = ctx.config.size
        grid: GridFields = bake_and_stamp(
            fields=ctx.fields,
            geometry=ctx.geometry,
            rivers=ctx.rivers,
            size=size,
            cfg=ctx.config.river,
        )

        # region_id is the persistence socket: present, schema-able, all -1.
        grid.region_id = np.full(size * size, -1, dtype=np.int32)

        leylines: LeylineNetwork | None = ctx.leylines
        if leylines is None:
            msg: str = "leylines must be set before assembling WorldData"
            raise RuntimeError(msg)

        return WorldData(
            seed=ctx.config.seed,
            size=size,
            config=ctx.config,
            grid=grid,
            rivers=ctx.rivers or [],
            lakes=ctx.lakes or [],
            leylines=leylines,
            landmasses=_build_landmasses(ctx, grid),
            volcanoes=ctx.volcanoes or [],
        )


# ``nearest_cell_per_tile`` is re-exported for the viewer, which bakes its own
# debug layers (e.g. mesh-side insolation) from the context.
__all__ = ["WorldgenPipeline", "nearest_cell_per_tile"]
