from dataclasses import replace
from random import Random

from src.core.mechanic.dice import RollResult, roll_pool
from src.core.mechanic.scaling import scale_threat
from src.core.model.threat import Channel
from src.state import GraphState


class DiceScaleNode:
    """One action roll; every threat is scaled from that single tier, each by
    its own position."""

    def __init__(self, *, rng: Random | None = None) -> None:
        self._rng: Random | None = rng

    async def __call__(self, state: GraphState) -> dict:
        pool: int = self._pool_for_attribute(state)
        roll_result: RollResult = roll_pool(pool, rng=self._rng)
        scaled = [
            replace(
                t,
                outcome=scale_threat(
                    base_magnitude=int(t.magnitude),
                    tier=roll_result.tier,
                    position=t.position,
                ),
            )
            for t in state.threats
        ]
        return {"roll_result": roll_result, "threats": scaled}

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