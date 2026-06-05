from dataclasses import replace
from random import Random

from src.core.mechanic.dice import roll_pool
from src.core.mechanic.economy import add_stress
from src.core.mechanic.narration_directive import resolution_directive
from src.core.mechanic.push import improve_magnitude, push_cost
from src.core.mechanic.threat_envelope import describe_threat
from src.core.model.resist import ResistAction
from src.core.model.threat import Threat
from src.state import GraphState, current_threat, pool_for


def _replace_threat(threats: list[Threat], updated: Threat) -> list[Threat]:
    return [updated if t.id == updated.id else t for t in threats]


class ResistRollNode:
    """Resolves the current threat, advances the cursor, and sets the directive
    for its resolution line. ENDURE pays nothing; RESIST rolls, pays stress, and
    improves this threat's magnitude by one. Stress/trauma thread across the
    cycle; trauma_gained / character_lost are OR-accumulated so a later clean
    iteration can't erase an earlier overflow."""

    def __init__(self, *, rng: Random | None = None) -> None:
        self._rng: Random | None = rng

    async def __call__(self, state: GraphState) -> dict:
        threat = current_threat(state)
        action = state.get("resist_action") or ResistAction.ENDURE
        flavor = state.get("resist_flavor") or ""

        updates: dict = {
            "resist_cursor": state.get("resist_cursor", 0) + 1,
            "narration_directive": resolution_directive(
                describe_threat(threat), action, flavor
            ),
        }
        if threat is None:
            return updates

        if action == ResistAction.ENDURE:
            updates["threats"] = _replace_threat(
                state.get("threats", []),
                replace(threat, resist_action=action, resist_flavor=flavor, resisted=False),
            )
            return updates

        roll = roll_pool(pool_for(state, threat.channel), rng=self._rng)
        cost = push_cost(roll.tier)
        stress_result = add_stress(state.get("stress", 0), state.get("trauma", 0), cost)
        updates.update(
            stress=stress_result.stress,
            trauma=stress_result.trauma,
            trauma_gained=state.get("trauma_gained", False) or stress_result.trauma_gained,
            character_lost=state.get("character_lost", False) or stress_result.lost,
        )

        new_threat = replace(
            threat,
            resist_action=action,
            resist_flavor=flavor,
            resist_roll=roll,
            resisted=True,
        )
        if threat.outcome is not None:
            new_mag = improve_magnitude(threat.outcome.landed_magnitude)
            new_threat = replace(new_threat, outcome=replace(threat.outcome, landed_magnitude=new_mag))
        updates["threats"] = _replace_threat(state.get("threats", []), new_threat)
        return updates