"""The final ``WorldData`` output contract.

The product entities (``River``, ``Lake``, ``Volcano``, ``Vein``, ``Nexus``,
``Region``, ``Landmass``) and their enums now live in ``core/model`` (they ship in
the persisted product).  ``WorldData`` stays here, in the producer: it is the
output *envelope* that aggregates the worldgen-owned ``Fields`` container and
``WorldgenConfig`` with the core-model entity lists.
"""

from dataclasses import dataclass

from src.core.model.environment.magic.nexus import Nexus
from src.core.model.environment.magic.vein import Vein
from src.core.model.environment.regions.region import Region
from src.core.model.environment.terrain.landmass import Landmass
from src.core.model.environment.terrain.volcano import Volcano
from src.core.model.environment.water.lake import Lake
from src.core.model.environment.water.river import River
from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.fields import Fields


@dataclass
class WorldData:
    """The final worldgen product handed to persistence.

    A resolved, self-describing snapshot: the ``config`` reproduces it from the
    same ``seed``/``size``.  The simulation mesh is intentionally absent — it is
    an internal intermediate (use ``WorldgenPipeline.run_debug`` for it).
    """

    seed: int  #: World seed.
    size: int  #: Gameplay grid edge length in tiles.
    config: WorldgenConfig  #: Resolved config snapshot (reproducibility).
    grid: Fields  #: Per-tile fields (the product surface).
    rivers: list[River]  #: River objects.
    lakes: list[Lake]  #: Lake objects.
    veins: list[Vein]  #: Leyline veins (mana drainage paths).
    nexuses: list[Nexus]  #: Nexus poles (ley-mantle extrema).
    landmasses: list[Landmass]  #: Connected land components (ocean excluded).
    volcanoes: list[Volcano]  #: Discrete volcanoes.
    regions: list[Region]  #: Named geographic regions; per-tile lookup is ``grid.region_id``.
