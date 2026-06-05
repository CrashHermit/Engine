from __future__ import annotations

from dataclasses import replace
from random import Random

from src.core.mechanic.dice import RollResult, roll_pool
from src.core.mechanic.scaling import scale_threat
from src.state import GraphState, pool_for


class DiceScaleNode:
    """Scale threats using decoupled offense and defense rolls.

    The action roll (on the action's attribute) is the offense — it feeds
    apply_effect downstream to land effect on the target. Each threat then
    gets its OWN independent defense roll on its own channel; that per-threat
    tier — not the shared action tier — scales the threat. A great action roll
    buys zero protection from an unrelated threat, and several threats no
    longer land at the same tier off one roll.
    """

    def __init__(self, *, rng: Random | None = None) -> None:
        self._rng: Random | None = rng

    async def __call__(self, state: GraphState) -> dict:
        # Offense: the action roll. Consumed by apply_effect (effect on target).
        action_roll: RollResult = roll_pool(
            pool_for(state, state.get("attribute")), rng=self._rng
        )
        # Defense: one independent roll per threat, on the threat's own channel.
        scaled = []
        for t in state.get("threats", []):
            defense: RollResult = roll_pool(pool_for(state, t.channel), rng=self._rng)
            scaled.append(
                replace(
                    t,
                    defense_roll=defense,
                    outcome=scale_threat(
                        base_magnitude=int(t.magnitude),
                        tier=defense.tier,
                        position=t.position,
                    ),
                )
            )
        return {"roll_result": action_roll, "threats": scaled}
