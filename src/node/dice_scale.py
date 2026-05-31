from random import Random

from src.core.mechanic.dice import roll_pool
from src.core.mechanic.scaling import scale_threat
from src.state import GraphState
from src.core.mechanic.dice import RollResult
from src.core.model.threat import Channel

class DiceScaleNode:
    def __init__(self, *, rng: Random | None = None) -> None:
        self._rng: Random = rng

    async def __call__(self, state: GraphState) -> dict:
        pool: int = self._pool_for_attribute(state)
        roll_result: RollResult = roll_pool(pool, rng=self._rng)
        outcome = scale_threat(
            base_magnitude=state.magnitude,
            tier=roll_result.tier,
            position=state.position,
        )
        return {
            "roll_result": roll_result,
            "outcome": outcome,
        }

    @staticmethod
    def _pool_for_attribute(state: GraphState) -> int:
        match state.attribute:
            case Channel.CORPUS:
                return state.corpus_rating
            case Channel.MENS:
                return state.mens_rating
            case Channel.ANIMA:
                return state.anima_rating
            case _:
                raise ValueError(f"unknown attribute: {state.attribute!r}")
