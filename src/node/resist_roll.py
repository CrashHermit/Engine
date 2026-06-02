from dataclasses import replace
from random import Random

from src.core.mechanic.dice import roll_pool
from src.core.mechanic.economy import add_stress
from src.core.mechanic.narration_directive import resolution_directive
from src.core.mechanic.push import improve_magnitude, push_cost
from src.core.mechanic.threat_envelope import describe_threat
from src.core.model.resist import ResistAction
from src.core.model.threat import Channel, Threat
from src.state import GraphState


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
        threat = state.current_threat
        action = state.resist_action or ResistAction.ENDURE
        flavor = state.resist_flavor or ""

        updates: dict = {
            "resist_cursor": state.resist_cursor + 1,
            "narration_directive": resolution_directive(
                describe_threat(threat), action, flavor
            ),
        }
        if threat is None:
            return updates

        if action == ResistAction.ENDURE:
            updates["threats"] = _replace_threat(
                state.threats,
                replace(threat, resist_action=action, resist_flavor=flavor, resisted=False),
            )
            return updates

        roll = roll_pool(self._pool_for_channel(threat.channel, state), rng=self._rng)
        cost = push_cost(roll.tier)
        stress_result = add_stress(state.stress, state.trauma, cost)
        updates.update(
            stress=stress_result.stress,
            trauma=stress_result.trauma,
            trauma_gained=state.trauma_gained or stress_result.trauma_gained,
            character_lost=state.character_lost or stress_result.lost,
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
        updates["threats"] = _replace_threat(state.threats, new_threat)
        return updates

    @staticmethod
    def _pool_for_channel(channel: Channel, state: GraphState) -> int:
        match channel:
            case Channel.CORPUS:
                return state.corpus_rating
            case Channel.MENS:
                return state.mens_rating
            case Channel.ANIMA:
                return state.anima_rating
            case _:
                return 0