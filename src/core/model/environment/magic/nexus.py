"""Nexus product entity: an enumerated extremum of the ley-mantle potential."""

from dataclasses import dataclass
from enum import StrEnum


class NexusPolarity(StrEnum):
    """A nexus pole's role in the mana flow (the sign of its ley-mantle extremum).

    ``SOURCE`` is a ley-mantle maximum (magic wells up — a headwater); ``SINK`` is
    a minimum (magic drains — a mouth).  Where the generator needs the signed value
    (+1 / −1) it maps from this label internally; the shipped entity carries the
    label, not an opaque integer.
    """

    SOURCE = "source"  # Ley-mantle maximum: magic wells up here.
    SINK = "sink"  # Ley-mantle minimum: magic drains here.


@dataclass
class Nexus:
    """A magic pole: an enumerated extremum of the ley-mantle potential.

    Built in Phase 4; ships on ``WorldData.nexuses`` and is the object the
    per-tile ``nexus_id`` column points back to.
    """

    id: int  #: Unique nexus identifier (0-based; matches ``nexus_id``).
    cell: int  #: Pole location (mesh cell id pre-bake; tile coords post-bake).
    polarity: NexusPolarity  #: Source (+) or sink (−).
    charge: float  #: [0,1] prominence of the extremum.
    channels: tuple[float, float, float]  #: Channel identity (corpus/mens/anima).
