from __future__ import annotations

from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.lm import lm
from src.state import GraphState


class SegmenterSignature(Signature):
    """You are a beat segmenter.

    The player's message has been determined to need a dice roll. Scope it down
    to the first contested beat:

    - lead_up: the mundane preamble before the first contested beat. Actions
      with no danger and no uncertainty (walking, drawing a weapon, opening
      an unlocked door, speaking with no social stakes). May be empty.
    - contested_beat: the SINGLE first action that carries both danger and
      uncertainty. Exactly one beat. This is what will be rolled. Anything the
      player stated AFTER this beat is intentionally dropped — only the first
      contested beat is resolved this turn.

    Rules:
    - contested_beat is always non-empty (the gate already decided a roll is needed).
    - If the message is a single contested action with no preamble,
      put it all in contested_beat and leave lead_up empty.
    - Do NOT paraphrase. Preserve the player's wording where possible.
    """

    message_history: str = InputField(
        default="", description="The conversation history so far"
    )
    human_message: str = InputField(description="The player's intended action")

    lead_up: str = OutputField(
        description="Mundane preamble before the first contested beat; may be empty"
    )
    contested_beat: str = OutputField(
        description="The single first contested action that will be rolled; non-empty"
    )


class SegmenterNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=SegmenterSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        history: str = "\n".join(m.format() for m in state.get("message_history", []))
        prediction: Prediction = await self._program.aforward(
            message_history=history,
            human_message=state.get("human_message").content,
        )
        return {
            "lead_up": prediction.lead_up.strip(),
            "contested_beat": prediction.contested_beat.strip(),
        }
