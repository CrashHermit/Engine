"""Lake product entity: a water-filled terrain depression."""

from dataclasses import dataclass


@dataclass
class Lake:
    """A water-balanced lake: a depression filled to its equilibrium level.

    A depression fills only as far as its catchment inflow can offset surface
    evaporation.  ``cells`` are the submerged cells (terrain below
    ``surface_level``), which may be a subset of the full geometric depression
    when the basin is endorheic (inflow < evaporation at the spill).  A lake
    that reaches its spill overflows and is exorheic (``outlet_cell`` set);
    one that equilibrates below the spill is endorheic (``outlet_cell`` None).
    ``cells``/``outlet_cell`` are mesh cell ids pre-bake and tile coordinates
    post-bake.
    """

    id: int  #: Unique lake identifier (0-based).
    cells: list[int]  #: Submerged cell/tile ids (terrain below the water surface).
    surface_level: float  #: Equilibrium water-surface elevation.
    outlet_cell: int | None  #: Spill cell if the lake overflows; ``None`` = endorheic.
    endorheic: bool = False  #: True when the lake equilibrates below its spill (no outflow).
    inflow: float = 0.0  #: Catchment inflow (accumulated upstream precipitation).
