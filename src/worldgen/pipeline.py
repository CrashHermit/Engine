import numpy as np

from src.worldgen.bake.features import features_to_tiles
from src.worldgen.bake.grid import bake_and_stamp, nearest_cell_per_tile
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.workspace import Workspace
from src.core.model.environment.magic.nexus import Nexus
from src.core.model.environment.magic.vein import Vein
from src.core.model.environment.regions.region import Region
from src.core.model.environment.terrain.landmass import Landmass
from src.worldgen.features import WorldData
from src.worldgen.fields import Fields
from src.worldgen.geometry.mesh import MeshGeometry, build_mesh
from src.worldgen.climate.insolation import InsolationStage
from src.worldgen.climate.moisture import MoistureStage
from src.worldgen.climate.ocean_current import OceanCurrentStage
from src.worldgen.climate.temperature import TemperatureStage
from src.worldgen.climate.wind import WindStage
from src.worldgen.ecology.biomes import BiomeStage
from src.worldgen.magic.savagery import SavageryStage
from src.worldgen.magic.stage import MagicStage
from src.worldgen.regions.regions import RegionsStage
from src.worldgen.stage import Stage
from src.worldgen.terrain.boundaries import BoundaryClassifyStage
from src.worldgen.terrain.boundary_uplift import BoundaryUpliftStage
from src.worldgen.terrain.erosion import ErosionStage
from src.worldgen.terrain.finalize import FinalizeStage
from src.worldgen.terrain.plate_personalities import PlatePersonalityStage
from src.worldgen.terrain.plates import PlatesStage
from src.worldgen.terrain.vulcanism import VolcanoesStage, VulcanismStage
from src.worldgen.water.discharge import DischargeStage
from src.worldgen.water.flow import FlowStage
from src.worldgen.water.lakes import LakesStage
from src.worldgen.water.rivers import RiversStage
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
        MagicStage(),
        BiomeStage(),
        # Phase 5 — derived regions (named gameplay socket; consumes finished fields)
        RegionsStage(),
    ]


def _validate_stage_deps(stages: list[Stage]) -> None:
    """Fail loudly at startup if a stage reads a field no earlier stage produced.

    With eager allocation every field is a zero array, so a misordered read would
    silently return zeros instead of raising.  This turns that into a construction-
    time error: each required read (``reads`` minus ``reads_optional``) must be in
    the union of earlier stages' ``writes`` or the stage's own ``writes``.
    ``reads_optional`` exempts deliberate zero-init forward references.
    """
    produced: set[str] = set()
    for stage in stages:
        writes: set[str] = set(stage.writes)
        required: set[str] = set(stage.reads) - set(getattr(stage, "reads_optional", ()))
        missing: set[str] = required - produced - writes
        if missing:
            name: str = type(stage).__name__
            msg: str = (
                f"{name} reads {sorted(missing)} but no earlier stage writes them "
                f"(stage misordered, or its reads/writes are mis-declared)"
            )
            raise RuntimeError(msg)
        produced |= writes


def _build_landmasses(ctx: Workspace, grid: Fields) -> list[Landmass]:
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
    ``Workspace`` for the viewer, which needs mesh-side intermediates.
    """

    def __init__(self, config: WorldgenConfig | None = None) -> None:
        self._config: WorldgenConfig | None = config

    def run(self, seed: int, size: int) -> WorldData:
        """Generate a world and return the product ``WorldData``."""
        world, _ctx = self.run_debug(seed=seed, size=size)
        return world

    def run_debug(self, seed: int, size: int) -> tuple[WorldData, Workspace]:
        """Generate a world and return ``(WorldData, Workspace)`` for debug.

        The viewer uses this door for mesh-side intermediates; the product
        ``run`` entry point throws the context (and its mesh) away.
        """
        ctx: Workspace = self._run_pipeline(seed=seed, size=size)
        world: WorldData = self._assemble(ctx)
        return world, ctx

    def _run_pipeline(self, seed: int, size: int) -> Workspace:
        """Build the mesh and run every stage; return the populated context."""
        cfg: WorldgenConfig = Workspace.resolve_config(
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
        fields: Fields = Fields.allocate(n=geometry.n_cells)
        ctx: Workspace = Workspace(config=cfg, geometry=geometry, fields=fields)

        stages: list[Stage] = _build_stages()
        _validate_stage_deps(stages)
        for stage in stages:
            stage.run(ctx)

        return ctx

    def _assemble(self, ctx: Workspace) -> WorldData:
        """Bake the grid, stamp rivers, and assemble the output ``WorldData``."""
        size: int = ctx.config.size
        grid: Fields = bake_and_stamp(
            fields=ctx.fields,
            geometry=ctx.geometry,
            rivers=ctx.outputs.rivers,
            size=size,
            cfg=ctx.config.river,
        )

        veins: list[Vein] | None = ctx.outputs.veins
        nexuses: list[Nexus] | None = ctx.outputs.nexuses
        if veins is None or nexuses is None:
            msg: str = "veins/nexuses must be set before assembling WorldData"
            raise RuntimeError(msg)

        regions: list[Region] | None = ctx.outputs.regions
        if regions is None:
            msg = "regions must be set before assembling WorldData"
            raise RuntimeError(msg)

        # Translate feature geometry from (ephemeral) mesh-cell ids to tile ids so
        # the shipped product is self-contained.  The bake/stamp above already
        # consumed the mesh-coordinate rivers, so this is the last step.
        rivers_t, lakes_t, veins_t, nexuses_t, volcanoes_t = features_to_tiles(
            geometry=ctx.geometry,
            size=size,
            rivers=ctx.outputs.rivers or [],
            lakes=ctx.outputs.lakes or [],
            veins=veins,
            nexuses=nexuses,
            volcanoes=ctx.outputs.volcanoes or [],
        )

        return WorldData(
            seed=ctx.config.seed,
            size=size,
            config=ctx.config,
            grid=grid,
            rivers=rivers_t,
            lakes=lakes_t,
            veins=veins_t,
            nexuses=nexuses_t,
            landmasses=_build_landmasses(ctx, grid),
            volcanoes=volcanoes_t,
            regions=regions,
        )


# ``nearest_cell_per_tile`` is re-exported for the viewer, which bakes its own
# debug layers (e.g. mesh-side insolation) from the context.
__all__ = ["WorldgenPipeline", "nearest_cell_per_tile"]
