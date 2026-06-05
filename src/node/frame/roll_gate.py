from __future__ import annotations

from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.lm import lm
from src.state import GraphState


class RollGateSignature(Signature):
    """You are a roll gate.

    Decide whether the player's intent for this beat needs a dice roll. A roll
    is needed only when the action carries BOTH danger and uncertainty:

    - Danger: failure or partial success would meaningfully cost the character
      (harm, complication, lost opportunity, position degradation).
    - Uncertainty: the outcome is genuinely in doubt given the character's
      capability, the situation, and the fiction.

    Mundane intent that has neither (walking to an unguarded room, picking up
    an obvious item, speaking a line with no social stakes) does NOT need a
    roll. Narrate it directly.

    Return true only when both danger and uncertainty are clearly present.
    Return false otherwise.
    """

    message_history: str = InputField(
        default="", description="The conversation history so far"
    )
    human_message: str = InputField(description="The player's intended action")

    needs_roll: bool = OutputField(
        description=(
            "Whether the beat needs a dice roll"
            " (true only when danger AND uncertainty are present)"
        )
    )


class RollGateNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=RollGateSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        history: str = "\n".join(m.format() for m in state.get("message_history", []))
        prediction: Prediction = await self._program.aforward(
            message_history=history,
            human_message=state.get("human_message").content,
        )
        updates: dict = {"needs_roll": prediction.needs_roll}
        if not prediction.needs_roll and state.get("human_message"):
            updates["lead_up"] = state.get("human_message").content
        return updates
