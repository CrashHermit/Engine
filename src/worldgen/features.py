"""Feature objects and the final ``WorldData`` output contract.

The feature dataclasses (``River``, ``Lake``, ``Landmass``, ``LeylineNetwork``)
are carried on the context during generation (``ctx.rivers``, ``ctx.lakes``,
``ctx.leylines``) and ship inside ``WorldData`` — the single product type the
pipeline hands to the persistence layer.
"""

from dataclasses import dataclass

from src.worldgen.config.worldgen_config import WorldgenConfig
from src.worldgen.fields import GridFields
from src.worldgen.types import Float64Array


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
