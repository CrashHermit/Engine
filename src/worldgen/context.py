from __future__ import annotations

import random
from dataclasses import dataclass

from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.data import WorldData
from src.worldgen.noise.sampler import PeriodicSampler


@dataclass
class WorldContext:
    """Shared context passed through every pipeline stage.

    Attributes:
        data: Mutable world state (mesh, grid, rivers, etc.).
        config: Fully-resolved pipeline configuration.
        rng: Seeded random instance for any stochastic stage logic.
        sampler: Shared ``PeriodicSampler`` with the correct world dimensions.
    """

    data: WorldData
    config: WorldgenConfig
    rng: random.Random
    sampler: PeriodicSampler

    @classmethod
    def build(
        cls,
        data: WorldData,
        config: WorldgenConfig | None = None,
    ) -> WorldContext:
        """Construct a ``WorldContext`` from world data, resolving defaults.

        Mesh ``width``/``height`` fall back to ``float(data.size)`` when the
        config leaves them at 0, keeping the mesh and grid in the same
        coordinate space.
        """
        cfg = config or WorldgenConfig()

        mesh_width = cfg.mesh.width or float(data.size)
        mesh_height = cfg.mesh.height or float(data.size)

        from dataclasses import replace

        resolved_mesh = replace(cfg.mesh, width=mesh_width, height=mesh_height)
        resolved = replace(cfg, seed=data.seed, size=data.size, mesh=resolved_mesh)

        return cls(
            data=data,
            config=resolved,
            rng=random.Random(data.seed),
            sampler=PeriodicSampler(
                width=mesh_width,
                height=mesh_height,
                seed=data.seed,
            ),
        )
