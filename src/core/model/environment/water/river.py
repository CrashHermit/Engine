"""River product entity: a labeled path through the receiver forest."""

from dataclasses import dataclass


@dataclass
class River:
    """A river as a labeled path through the receiver forest.

    The receiver array encodes a forest (each cell points at one parent).
    Rivers are the labeled paths through it: sources start new rivers, at
    junctions the larger-discharge inflow keeps the river identity and smaller
    ones record ``tributary_of``.  Numeric payloads are plain Python (numpy-free,
    serialization-ready); ``cells``/``mouth`` are mesh cell ids pre-bake and tile
    coordinates post-bake.
    """

    id: int  #: Unique river identifier (0-based).
    cells: list[int]  #: Source → mouth, contiguous cell/tile ids.
    discharge: tuple[float, ...]  #: Per-cell discharge along the path (same length as ``cells``).
    mouth: int  #: Where the river terminates (ocean, lake, or non-river cell).
    tributary_of: int | None  #: River id this river joins; ``None`` for trunk rivers.
