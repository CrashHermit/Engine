import random

from src.core.mechanics import Magnitude, Position, roll_pool, scale_threat
from src.core.model.resolution import Attribute
from src.state import GraphState


class ResolutionNode:
    """Deterministic resolution (decisions #7, #15-17): the join after the framing
    fan-out. Reads the classified `attribute` + `base_magnitude` from state, rolls
    that attribute's pool, and scales the pre-set threat by the result. No LLM —
    the dice and scaling come straight from the Phase-0 mechanics core.

    Falls back to safe defaults if framing is missing (e.g. a future path that
    skips the fan-out), so the node never crashes the turn.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng

    async def __call__(self, state: GraphState) -> dict:
        attribute = state.attribute or Attribute.CORPUS.value
        rating = int(getattr(state, attribute, 0))
        base_magnitude = state.base_magnitude if state.base_magnitude is not None else int(Magnitude.STANDARD)

        result = roll_pool(rating, rng=self._rng)
        outcome = scale_threat(base_magnitude, result.tier, Position.RISKY)

        return {
            "roll_dice": list(result.dice),
            "roll_tier": result.tier.value,
            "landed_magnitude": outcome.landed_magnitude,
            "outcome_avoided": outcome.avoided,
            "outcome_crit": outcome.crit,
        }
