import random

from dspy import Predict
from dspy.primitives.prediction import Prediction

from src.core.mechanics import improve_magnitude, push_cost, roll_pool
from src.core.model.resolution import Attribute
from src.lm import lm
from src.signatures.resist_parser import ResistParserSignature
from src.state import GraphState


class ResistParserNode:
    """Parse a resistance-offer reply (decision #6). Mirrors the intent-alignment
    re-invoke loop: the offer lived on the prior turn, the player's typed reply
    re-enters here. Pure classification — no effects applied.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ResistParserSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        consequence = "\n".join(m.format() for m in state.resistance_history)
        prediction: Prediction = await self._program.aforward(
            consequence=consequence,
            player_reply=state.human_message.content,
        )
        return {"resist_decision": bool(prediction.is_resisting)}


class ResistResolutionNode:
    """Deterministic resist/push (decisions #11). Roll the threat's channel; the
    improvement always lands (one magnitude reduced) and the dice only set the
    stress price. Emits the reduced magnitude + the stress cost as *intended*
    effects; the TUI applies the stress via EconomyService (decision #21).
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng

    async def __call__(self, state: GraphState) -> dict:
        if not state.resist_decision:
            # Player declined: the consequence stands, no cost.
            return {"stress_delta": 0}

        channel = state.threat_channel or Attribute.CORPUS.value
        rating = int(getattr(state, channel, 0))
        result = roll_pool(rating, rng=self._rng)
        cost = push_cost(result.tier)
        reduced = improve_magnitude(state.landed_magnitude or 0, steps=1)

        return {
            "landed_magnitude": reduced,
            "stress_delta": cost,
            "roll_dice": list(result.dice),
            "roll_tier": result.tier.value,
        }
