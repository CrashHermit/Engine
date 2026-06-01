from dataclasses import replace
from random import Random

from src.core.mechanic.dice import roll_pool
from src.core.mechanic.economy import add_stress
from src.core.mechanic.push import improve_magnitude, push_cost
from src.core.mechanic.scaling import Outcome
from src.core.model.resist import ResistAction
from src.core.model.threat import Channel
from src.state import GraphState


class ResistRollNode:
    def __init__(self, *, rng: Random | None = None) -> None:
        self._rng = rng

    async def __call__(self, state: GraphState) -> dict:
        if state.resist_action == ResistAction.ENDURE:
            return {}

        pool = self._pool_for_channel(state)
        roll = roll_pool(pool, rng=self._rng)
        cost = push_cost(roll.tier)
        stress_result = add_stress(state.stress, state.trauma, cost)

        updates: dict = {
            "resist_roll_result": roll,
            "stress": stress_result.stress,
            "trauma": stress_result.trauma,
            "trauma_gained": stress_result.trauma_gained,
            "character_lost": stress_result.lost,
        }

        if state.resist_action == ResistAction.RESIST and state.outcome is not None:
            new_mag = improve_magnitude(state.outcome.landed_magnitude)
            updates["outcome"] = replace(state.outcome, landed_magnitude=new_mag)

        return updates

    def _pool_for_channel(self, state: GraphState) -> int:
        match state.threat_channel:
            case Channel.CORPUS:
                return state.corpus_rating
            case Channel.MENS:
                return state.mens_rating
            case Channel.ANIMA:
                return state.anima_rating
            case _:
                return 0
