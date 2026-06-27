"""Landmass product entity: a connected land component, summarized."""

from dataclasses import dataclass


@dataclass
class Landmass:
    """A connected land component, summarized for the output contract.

    Built from the per-cell ``landmass_id`` / ``landmass_class``.  Ocean
    (component 0) is not a landmass.
    """

    id: int  #: 1-based connected-component id (matches ``landmass_id``).
    cell_count: int  #: Number of mesh cells in the component.
    tile_count: int  #: Number of grid tiles the component covers.
    landmass_class: int  #: 1 = island, 2 = landmass, 3 = major.
