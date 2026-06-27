"""Vein product entity: a labeled path through the mana flow tree."""

from dataclasses import dataclass


@dataclass
class Vein:
    """A leyline as a labeled path through the mana flow tree.

    The magic mirror of :class:`~src.core.model.environment.water.river.River`:
    veins are the high-accumulation paths through the receiver forest over the ley
    potential.  Numeric payloads are plain Python (numpy-free); ``cells`` are mesh
    cell ids pre-bake and tile coordinates post-bake.
    """

    id: int  #: Unique vein identifier (0-based; matches ``vein_id``).
    cells: list[int]  #: Source → mouth, contiguous cell/tile ids.
    strength: tuple[float, ...]  #: Per-cell magic strength along the vein.
    channels: tuple[tuple[float, float, float], ...]  #: Per-cell channel composition.
    source_nexus: int  #: Nexus id at the headwater; ``-1`` if not a pole.
    mouth_nexus: int | None  #: Sink nexus id the vein drains into; ``None`` otherwise.
    tributary_of: int | None  #: Vein id this vein joins; ``None`` for trunk veins.
