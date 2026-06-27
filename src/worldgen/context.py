from dataclasses import dataclass, replace

from src.worldgen.config.worldgen_config import MeshConfig
from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.features import Lake, Nexus, Region, River, Vein, Volcano
from src.worldgen.fields import Fields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.rng import NoiseSource, subseed
from src.worldgen.terrain.boundaries import BoundaryFacts
from src.worldgen.terrain.plate_personalities import PlateProperties
from src.worldgen.terrain.vulcanism import VolcanoSeed
from src.worldgen.types import Float64Array


@dataclass
class WorldContext:
    """Shared state for the worldgen pipeline"""

    config: WorldgenConfig
    geometry: MeshGeometry
    fields: Fields
    plate_properties: PlateProperties | None = None
    boundary_facts: BoundaryFacts | None = None
    volcano_candidates: list[VolcanoSeed] | None = None  # pre-erosion seeds; materialized post-finalize
    volcanoes: list[Volcano] | None = None
    rivers: list[River] | None = None
    lakes: list[Lake] | None = None
    veins: list[Vein] | None = None
    nexuses: list[Nexus] | None = None
    magic_potential: Float64Array | None = None  # combined ley potential (mesh intermediate, for the viewer/tests)
    regions: list[Region] | None = None

    def seed_for(self, name: str) -> int:
        """Deterministic sub-seed for a named stage or purpose."""
        return subseed(seed=self.config.seed, name=name)

    def noise_for(self, name: str) -> NoiseSource:
        """NoiseSource scoped to this world's torus and sub-seed."""
        return NoiseSource(
            seed=self.seed_for(name),
            width=self.geometry.width,
            height=self.geometry.height,
        )

    @staticmethod
    def resolve_config(
        seed: int, size: int, config: WorldgenConfig | None = None
    ) -> WorldgenConfig:
        """Apply seed/size and resolve mesh width/height from config."""
        cfg: WorldgenConfig = config or WorldgenConfig()
        mesh_width: float = cfg.mesh.width or float(size)
        mesh_height: float = cfg.mesh.height or float(size)
        # cell_count == 0 means "derive from size": one cell per tile (parity),
        # capped so large worlds stay within a sane gen-time budget.
        resolved_cells: int = cfg.mesh.cell_count or min(
            size * size, cfg.mesh.cell_count_cap
        )
        resolved_mesh: MeshConfig = replace(
            cfg.mesh,
            cell_count=resolved_cells,
            width=mesh_width,
            height=mesh_height,
        )
        return replace(cfg, seed=seed, size=size, mesh=resolved_mesh)
