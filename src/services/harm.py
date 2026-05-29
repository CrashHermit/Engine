from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.mechanics.harm import DEFAULT_CAPACITY, WoundPool, WoundThresholds, distal_parts
from src.core.model.part import Status
from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository
from src.database.repository.part import PartRepository

if TYPE_CHECKING:
    from arcadedb_embedded.graph import Vertex


@dataclass(frozen=True)
class HarmResult:
    part_name: str
    filled: int
    status: Status
    destroyed: bool
    overflow: int               # boxes past capacity (death signal on a vital part, #13)
    severed_parts: list[str]    # parts removed from the graph (DESTROYED + everything distal)


class HarmService:
    """Applies persistent harm to a body part (decision #19, model "C").

    Composes the pure `WoundPool` (fill boxes -> derive Status) with the part
    graph: a DESTROYED part is severed along with everything distal to it
    (`distal_parts`). Graph nodes stay pure and emit an *intended* harm
    (part + magnitude); this service is the single write path that applies it
    (decision #21), inside one transaction.
    """

    def __init__(
        self,
        base: BaseRepository,
        parts: PartRepository,
        characters: CharacterRepository,
        *,
        default_capacity: int = DEFAULT_CAPACITY,
        thresholds: WoundThresholds = WoundThresholds(),
    ) -> None:
        self._base = base
        self._parts = parts
        self._characters = characters
        self._default_capacity = default_capacity
        self._thresholds = thresholds

    def _require_character(self, character_id: str) -> Vertex:
        character = self._characters.get_character(character_id)
        if character is None:
            raise ValueError(f"Character not found: {character_id}")
        return character

    def apply_harm(self, character_id: str, part_name: str, magnitude: int) -> HarmResult:
        character = self._require_character(character_id)
        part = self._parts.get_part(character, part_name)
        if part is None:
            raise ValueError(f"Part not found on character: {part_name}")

        pool = WoundPool(
            capacity=self._parts.get_capacity(part, self._default_capacity),
            filled=self._parts.get_wound_boxes(part),
            thresholds=self._thresholds,
        )
        overflow = pool.apply(magnitude)
        severed: list[str] = []

        with self._base.transaction():
            if pool.destroyed:
                severed = self._sever(character, part)
            else:
                self._parts.set_wound_state(part, filled=pool.filled, status=pool.status.value)

        return HarmResult(
            part_name=part_name,
            filled=pool.filled,
            status=pool.status,
            destroyed=pool.destroyed,
            overflow=overflow,
            severed_parts=severed,
        )

    def _sever(self, character: Vertex, root: Vertex) -> list[str]:
        """Remove a DESTROYED part and everything distal to it from the graph."""
        # Build the name -> attached-names map for the pure traversal.
        parts = self._parts.list_parts(character)
        attached = {
            p.get(name="name"): [c.get(name="name") for c in self._parts.attached_parts(p)]
            for p in parts
        }
        doomed = distal_parts(root.get(name="name"), attached)

        by_name = {p.get(name="name"): p for p in parts}
        for name in doomed:
            part = by_name.get(name)
            if part is not None:
                self._parts.remove_part(part)
        return sorted(doomed)
