from dataclasses import replace
from random import Random

from src.core.mechanic.dice import RollResult, roll_pool
from src.core.mechanic.scaling import scale_threat
from src.state import GraphState


class DiceScaleNode:
    """One action roll; every threat is scaled from that single tier, each by
    its own position."""

    def __init__(self, *, rng: Random | None = None) -> None:
        self._rng: Random | None = rng

    async def __call__(self, state: GraphState) -> dict:
        roll_result: RollResult = roll_pool(state.pool_for(state.attribute), rng=self._rng)
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
