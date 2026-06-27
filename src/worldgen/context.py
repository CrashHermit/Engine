from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from src.core.model.environment.magic.nexus import Nexus
from src.core.model.environment.magic.vein import Vein
from src.core.model.environment.regions.region import Region
from src.core.model.environment.terrain.volcano import Volcano
from src.core.model.environment.water.lake import Lake
from src.core.model.environment.water.river import River
from src.worldgen.config.worldgen_config import MeshConfig, WorldgenConfig
from src.worldgen.fields import Fields
from src.worldgen.geometry.mesh import MeshGeometry
from src.worldgen.noise.rng import NoiseSource, subseed
from src.worldgen.types import Float64Array

if TYPE_CHECKING:
    # Scratch types defined in terrain algorithm modules.  Imported for
    # annotations only, under TYPE_CHECKING, so co-located terrain stages can
    # import WorldContext without an import cycle (the terrain modules host both
    # the algorithm and its Stage; this context only *references* their types).
    from src.worldgen.terrain.boundaries import BoundaryFacts
    from src.worldgen.terrain.plate_personalities import PlateProperties
    from src.worldgen.terrain.vulcanism import VolcanoSeed


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
