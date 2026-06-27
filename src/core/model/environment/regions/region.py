"""Region product entity: a named, gameplay-addressable area from geography."""

from dataclasses import dataclass
from enum import StrEnum

from src.core.model.environment.ecology.biome import BiomeEnum


class RegionKind(StrEnum):
    """What a ``Region`` is — the taxonomy gameplay hooks (quests, lore) key on.

    A small, *extensible* enum: the geography-stable kinds (land bodies, ocean
    bodies) plus the biome-region landscapes.  Region kinds may overlap; the
    per-tile ``region_id`` carries the *primary* (geographic-body) partition.
    """

    LANDMASS = "landmass"  #: A connected body of dry land (continent / island).
    OCEAN = "ocean"  #: A connected body of open sea (ocean / sea / gulf).
    # Biome-regions: connected runs of one landscape category, overlapping the
    # land bodies above (per-tile lookup is the separate ``biome_region_id``).
    FOREST = "forest"  #: Forests, taigas, woodlands, rainforests, jungles.
    GRASSLAND = "grassland"  #: Prairies, steppes, savannas — open "plains".
    DESERT = "desert"  #: Hot/cold deserts, badlands, wastelands.
    TUNDRA = "tundra"  #: Frigid barrens, ice, polar desert.
    WETLAND = "wetland"  #: Bogs, mires, marshes, swamps, mangroves.
    SHRUBLAND = "shrubland"  #: Scrub, chaparral, sagebrush, thorn.


@dataclass
class Region:
    """A named, gameplay-addressable area derived from geography.

    The "socket" entity: a stable handle (``id`` ↔ per-tile ``region_id``) that
    quests, cities, and borders reference, independent of how the underlying
    fields churn.
    """

    id: int  #: Global region id (0-based); matches the per-cell/per-tile id columns.
    kind: RegionKind  #: What this region is (see :class:`RegionKind`).
    name: str  #: Display name (deterministic from seed + id).
    cell_count: int  #: Number of mesh cells in the region.
    centroid: tuple[float, float]  #: Torus-aware center in world units (wraps correctly).
    dominant_biome: BiomeEnum | None = None  #: Most common biome (biome-regions only; else None).
