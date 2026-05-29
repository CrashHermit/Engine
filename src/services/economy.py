from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.mechanics.economy import (
    EconomyConfig,
    StressResult,
    ViceResult,
    add_stress,
    vice_clear,
)
from src.database.repository.base import BaseRepository
from src.database.repository.character import CharacterRepository

if TYPE_CHECKING:
    from arcadedb_embedded.graph import Vertex


class EconomyService:
    """Persists the survival economy (decisions #11-14).

    Composes the pure `economy` mechanics (stress overflow -> trauma -> lost;
    vice-clear + overindulge) with the CHARACTER vertex's stored stress / trauma /
    vices. Graph nodes stay pure and emit *intended* stress deltas; this service is
    the single write path that applies them (decision #21), inside one transaction.
    """

    def __init__(
        self,
        base: BaseRepository,
        characters: CharacterRepository,
        config: EconomyConfig = EconomyConfig(),
    ) -> None:
        self._base = base
        self._characters = characters
        self._config = config

    def _require(self, character_id: str) -> Vertex:
        character = self._characters.get_character(character_id)
        if character is None:
            raise ValueError(f"Character not found: {character_id}")
        return character

    def add_stress(self, character_id: str, amount: int) -> StressResult:
        """Apply a stress gain; overflow trades into trauma and may lose the
        character. On a new trauma, a coping vice is granted (decision #14)."""
        character = self._require(character_id)
        result = add_stress(
            stress=self._characters.get_stress(character),
            trauma=self._characters.get_trauma(character),
            amount=amount,
            config=self._config,
        )
        vices = self._characters.get_vices(character)
        if result.trauma_gained:
            vices = vices + [self._coping_vice(result.trauma)]
        with self._base.transaction():
            self._characters.set_economy(
                character,
                stress=result.stress,
                trauma=result.trauma,
                vices=vices,
            )
        return result

    def clear_stress(self, character_id: str, vice_roll: int) -> ViceResult:
        """Indulge a vice: clear stress equal to the vice roll; overshooting current
        stress overindulges (decision #12). The caller rolls the lowest attribute."""
        character = self._require(character_id)
        result = vice_clear(self._characters.get_stress(character), vice_roll)
        with self._base.transaction():
            self._characters.set_economy(
                character,
                stress=result.stress,
                trauma=self._characters.get_trauma(character),
                vices=self._characters.get_vices(character),
            )
        return result

    def add_vice(self, character_id: str, vice: str) -> None:
        """Add a freeform vice (e.g. the starting vice, decision #14)."""
        character = self._require(character_id)
        with self._base.transaction():
            self._characters.set_economy(
                character,
                stress=self._characters.get_stress(character),
                trauma=self._characters.get_trauma(character),
                vices=self._characters.get_vices(character) + [vice],
            )

    @staticmethod
    def _coping_vice(trauma_level: int) -> str:
        """A placeholder coping-vice descriptor born from a trauma (#14).

        Freeform by design; a later pass can have the narrator author these in the
        fiction. Numbered so accumulation is visible until then.
        """
        return f"coping mechanism #{trauma_level}"
