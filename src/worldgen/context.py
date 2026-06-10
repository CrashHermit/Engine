from __future__ import annotations

import random
from dataclasses import dataclass, replace

from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.model import WorldData, WorldSpec
from src.worldgen.noise.sampler import PeriodicSampler


@dataclass
class WorldContext:
    """Shared context passed through every pipeline stage.

    Attributes:
        spec: Immutable pipeline input (size, seed, name).
        data: Mutable world state being built (mesh, grid, rivers, etc.).
        config: Fully-resolved pipeline configuration.
        rng: Seeded random instance for any stochastic stage logic.
        sampler: Shared ``PeriodicSampler`` with the correct world dimensions.
    """

    spec: WorldSpec
    data: WorldData
    config: WorldgenConfig
    rng: random.Random
    sampler: PeriodicSampler

    @classmethod
    def build(
        cls,
        spec: WorldSpec,
        config: WorldgenConfig | None = None,
    ) -> WorldContext:
        """Construct a ``WorldContext`` from a ``WorldSpec``, resolving defaults.

        Mesh ``width``/``height`` fall back to ``float(spec.size)`` when the
        config leaves them at 0, keeping the mesh and grid in the same
        coordinate space.
        """
        cfg = config or WorldgenConfig()

        mesh_width = cfg.mesh.width or float(spec.size)
        mesh_height = cfg.mesh.height or float(spec.size)

        resolved_mesh = replace(cfg.mesh, width=mesh_width, height=mesh_height)
        resolved = replace(cfg, seed=spec.seed, size=spec.size, mesh=resolved_mesh)

        return cls(
            spec=spec,
            data=WorldData(),
            config=resolved,
            rng=random.Random(spec.seed),
            sampler=PeriodicSampler(
                width=mesh_width,
                height=mesh_height,
                seed=spec.seed,
            ),
        )
