"""Lake product entity: a water-filled terrain depression."""

from dataclasses import dataclass


@dataclass
class Lake:
    """A lake as a connected component of water-filled terrain depressions.

    A lake is a connected blob of cells where ``z_route > z + epsilon``, its
    surface is their shared ``z_route`` value, and its outlet is the spill cell
    where water would overflow.  ``cells``/``outlet_cell`` are mesh cell ids
    pre-bake and tile coordinates post-bake.
    """

    id: int  #: Unique lake identifier (0-based).
    cells: list[int]  #: Cell/tile ids belonging to the lake.
    surface_level: float  #: Shared ``z_route`` value of lake cells.
    outlet_cell: int | None  #: Spill cell; ``None`` = terminal (endorheic) lake.
