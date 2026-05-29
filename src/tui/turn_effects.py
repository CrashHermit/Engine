"""The integration boundary: apply a turn's intended effects via services, and
compute what carries to the next turn (decisions #21, #10, #6).

Graph nodes stay pure — they emit *intended* effects into the result dict
(`harm_part` + `landed_magnitude`, `stress_delta`, `deferred_tail`, ...). After
`ainvoke`, the TUI calls into here, which owns the actual writes via services.
Kept free of any Textual import so it is unit-testable without a running app.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# A consequence is worth offering resistance against at Standard magnitude or
# worse (decision #6 — "significant + resistible").
_RESISTIBLE_FROM = 2


@dataclass(frozen=True)
class TurnCarry:
    """What survives into the next turn — lives on GameScreen, not in graph state
    (the TUI rebuilds GraphState each turn, so cross-turn carry is the screen's
    job, per the design's cross-cutting notes)."""

    pending_intent: str = ""                 # deferred tail, surfaced as a hint (#10)
    resistance_consequence: str | None = None  # a landed consequence to offer resisting (#6)


def apply_turn_effects(
    result: dict[str, Any],
    services: Any,
    character_id: str,
) -> list[str]:
    """Apply the turn's intended mechanical effects to persistent state, returning
    short human-readable notes (for the log). The single write path (decision #21).

    Resilient by design: a missing service, a part that no longer exists, or an
    absent character is reported as a note rather than crashing the turn.
    """
    notes: list[str] = []

    landed = result.get("landed_magnitude") or 0
    avoided = bool(result.get("outcome_avoided"))

    # Harm: a harm-type threat that actually lands fills `landed` wound boxes on
    # the chosen part (decision #19). `harm_part` is set by the (still-open)
    # harm-location step; until that ships, harm simply isn't applied here.
    harm_part = result.get("harm_part")
    if (
        harm_part
        and not avoided
        and landed > 0
        and result.get("threat_type") == "harm"
        and getattr(services, "harm", None) is not None
    ):
        try:
            hr = services.harm.apply_harm(character_id, harm_part, landed)
            if hr.destroyed:
                severed = ", ".join(hr.severed_parts)
                notes.append(f"{harm_part} destroyed (lost: {severed})")
            else:
                notes.append(f"{harm_part} → {hr.status.value} ({hr.filled} boxes)")
        except ValueError as e:
            notes.append(f"harm not applied: {e}")

    # Stress: push/resist cost or a stress consequence (decisions #11-14).
    stress_delta = result.get("stress_delta") or 0
    if stress_delta and getattr(services, "economy", None) is not None:
        try:
            sr = services.economy.add_stress(character_id, stress_delta)
            if sr.lost:
                notes.append("character is lost (max trauma)")
            elif sr.trauma_gained:
                notes.append(f"trauma {sr.trauma} (+coping vice); stress reset")
            else:
                notes.append(f"stress +{stress_delta} → {sr.stress}")
        except ValueError as e:
            notes.append(f"stress not applied: {e}")

    return notes


def next_turn_carry(result: dict[str, Any]) -> TurnCarry:
    """Decide what carries to the next turn: the deferred tail (#10) and whether a
    landed consequence should be offered for resistance (#6)."""
    tail = (result.get("deferred_tail") or "").strip()

    consequence: str | None = None
    landed = result.get("landed_magnitude") or 0
    if not result.get("outcome_avoided") and landed >= _RESISTIBLE_FROM:
        threat = result.get("threat_type") or "consequence"
        consequence = result.get("ai_message_content") or f"a {threat} of magnitude {landed}"

    return TurnCarry(pending_intent=tail, resistance_consequence=consequence)
