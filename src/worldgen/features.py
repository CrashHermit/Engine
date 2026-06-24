"""Feature objects and the final ``WorldData`` output contract.

The feature dataclasses (``River``, ``Lake``, ``Landmass``, ``LeylineNetwork``)
are carried on the context during generation (``ctx.rivers``, ``ctx.lakes``,
``ctx.leylines``) and ship inside ``WorldData`` — the single product type the
pipeline hands to the persistence layer.
"""

from dataclasses import dataclass
from enum import IntEnum

from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.fields import GridFields
from src.worldgen.types import Float64Array


class VolcanoKind(IntEnum):
    """Volcano morphology, derived from its generating mechanism."""

    STRATO = 0   # subduction arc — steep composite cone
    SHIELD = 1   # hotspot — broad basaltic shield
    FISSURE = 2  # rift / mid-ocean ridge — fissure eruption


class VolcanoStatus(IntEnum):
    """Present-day activity of a volcano."""

    ACTIVE = 0
    DORMANT = 1
    EXTINCT = 2


@dataclass
class Volcano:
    """A discrete volcano in mesh-cell coordinates.

    Built by the vulcanism stage; ships on ``WorldData.volcanoes`` and is the
    object the per-tile ``volcano_id`` column points back to.
    """

    id: int  #: Unique volcano identifier (0-based; matches ``volcano_id``).
    cell: int  #: Mesh cell id of the summit.
    kind: VolcanoKind  #: Morphology (from mechanism).
    status: VolcanoStatus  #: Active / dormant / extinct.
    chain_id: int  #: Arc or hotspot trail grouping; ``-1`` = solitary.
    activity: float  #: [0,1] present-day activity at the summit.
    has_caldera: bool  #: Summit caldera forces a crater lake (set in VP2).


@dataclass
class River:
    """A river as a labeled path through the receiver forest.

    The receiver array encodes a forest (each cell points at one parent).
    Rivers are the labeled paths through it: sources start new rivers,
    at junctions the larger-discharge inflow keeps the river identity
    and smaller ones record ``tributary_of``.
    """

    id: int  #: Unique river identifier (0-based).
    cells: list[int]  #: Source → mouth, mesh cell ids (contiguous).
    discharge: Float64Array  #: Per-cell discharge along the river path (same length as ``cells``).
    mouth: int  #: Cell id where the river terminates (ocean, lake, or non-river cell).
    tributary_of: int | None  #: River id this river joins; ``None`` for trunk rivers.


@dataclass
class Lake:
    """A lake as a connected component of water-filled terrain depressions.

    A lake is a connected blob of cells where ``z_route > z + epsilon``,
    its surface is their shared ``z_route`` value, and its outlet is the
    spill cell where water would overflow.
    """

    id: int  #: Unique lake identifier (0-based).
    cells: list[int]  #: Mesh cell ids belonging to the lake.
    surface_level: float  #: Shared ``z_route`` value of lake cells.
    outlet_cell: int | None  #: Spill cell; ``None`` = terminal (endorheic) lake.


@dataclass
class LeylineNetwork:
    """The magic web: scored nexus cells, their aspects, and the edges between.

    Built in Phase 4 (nexus placement → MST + loops → aspect assignment).
    ``edges`` index into ``nexus_cells``, not raw mesh cell ids.
    """

    nexus_cells: list[int]  #: Mesh cell ids of the placed nexuses.
    nexus_valence: Float64Array  #: Per-nexus valence in [-1, 1] (corrupt..pure).
    nexus_channels: Float64Array  #: Per-nexus channel weights, shape (k, 3).
    edges: list[tuple[int, int]]  #: Leyline edges as index pairs into ``nexus_cells``.


@dataclass
class Landmass:
    """A connected land component, summarized for the output contract.

    Built from the per-cell ``landmass_id`` / ``landmass_class`` written by
    ``terrain/finalize.py``.  Ocean (component 0) is not a landmass.
    """

    id: int  #: 1-based connected-component id (matches ``landmass_id``).
    cell_count: int  #: Number of mesh cells in the component.
    tile_count: int  #: Number of grid tiles the component covers.
    landmass_class: int  #: 1 = island, 2 = landmass, 3 = major.


class RegionKind(IntEnum):
    """What a ``Region`` is — the taxonomy gameplay hooks (quests, lore) key on.

    A small, *extensible* enum: the socket ships the geography-stable kinds whose
    inputs are settled (land bodies, ocean bodies).  Ecology- and weather-derived
    kinds (forests, plains, marine biomes, ...) slot in later as their fields
    mature, without changing the contract.  Region kinds are allowed to overlap;
    the per-tile ``region_id`` carries the *primary* (geographic-body) partition.
    """

    LANDMASS = 0  #: A connected body of dry land (continent / island).
    OCEAN = 1  #: A connected body of open sea (ocean / sea / gulf).


@dataclass
class Region:
    """A named, gameplay-addressable area derived from geography.

    The "socket" entity: a stable handle (``id`` ↔ per-tile ``region_id``) that
    quests, cities, and borders reference, independent of how the underlying
    fields churn.  Region extraction is a cheap derived pass over the mesh, so
    new kinds and richer naming can be added without touching the contract.
    """

    id: int  #: Global region id (0-based); matches the per-cell/per-tile ``region_id``.
    kind: RegionKind  #: What this region is (see :class:`RegionKind`).
    name: str  #: Display name (deterministic from seed + id; a placeholder namer for now).
    cell_count: int  #: Number of mesh cells in the region.
    centroid: tuple[float, float]  #: Torus-aware center in world units (wraps correctly).


@dataclass
class WorldData:
    """The final worldgen product handed to persistence.

    A resolved, self-describing snapshot: the ``config`` reproduces it from the
    same ``seed``/``size``.  The simulation mesh is intentionally absent — it is
    an internal intermediate (use ``WorldgenPipeline.run_debug`` for it).
    Feature objects stay in mesh-cell coordinates; per-tile lookup is the baked
    ``river_id`` / ``lake_id`` columns on ``grid``.
    """

    seed: int  #: World seed.
    size: int  #: Gameplay grid edge length in tiles.
    config: WorldgenConfig  #: Resolved config snapshot (reproducibility).
    grid: GridFields  #: Per-tile fields (the product surface).
    rivers: list[River]  #: River objects in mesh-cell coordinates.
    lakes: list[Lake]  #: Lake objects in mesh-cell coordinates.
    leylines: LeylineNetwork  #: The magic web.
    landmasses: list[Landmass]  #: Connected land components (ocean excluded).
    volcanoes: list[Volcano]  #: Discrete volcanoes in mesh-cell coordinates.
    regions: list[Region]  #: Named geographic regions; per-tile lookup is ``grid.region_id``.
