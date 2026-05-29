"""Pure, Textual-free view helpers for the TUI, so they can be unit-tested
without a running app (Textual widgets can't be imported headless)."""

from __future__ import annotations

from src.core.model.character import CharacterData


def format_condition(character: CharacterData, *, stress_max: int = 9, trauma_max: int = 4) -> str:
    """One-line survival-economy summary for the character sheet (decisions
    #11-14). Vices are listed when present — they accumulate as a scar-record
    (decision #14)."""
    vices = ", ".join(character.vices) if character.vices else "—"
    return (
        f"Stress: {character.stress} / {stress_max}  |  "
        f"Trauma: {character.trauma} / {trauma_max}  |  "
        f"Vices: {vices}"
    )
