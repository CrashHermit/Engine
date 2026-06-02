from dspy import Predict, Prediction

from src.core.model.message import Message
from src.lm import lm
from src.signature.narrator import NarratorSignature
from src.state import GraphState


class NarratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=NarratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        history = "\n".join(m.format() for m in state.message_history)
        entities = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        directive = state.narration_directive or ""
        # A suspended foe coming back this turn is narrated first (it re-enters
        # the scene), then the action's effect outcome.
        if state.reengagement_note:
            directive = f"{directive}\n\nA neutralized foe returns: {state.reengagement_note}"
        # The effect-on-target outcome (kill / disarm / rout / evade …) is a
        # structural instruction so prose can't recast a rout as a kill.
        if state.resolution_outcome:
            directive = f"{directive}\n\nResolution of the action on its target: {state.resolution_outcome}"
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=history,
            contested_beat=state.contested_beat or "",
            narration_directive=directive,
            anchors=state.anchors or "",
            prior_prose=state.prior_prose or "",
        )
        text = prediction.ai_message.strip()
        ai_message = Message(role="ai", content=text, name="Narrator")
        return {
            "ai_message": ai_message,
            "prior_prose": text,
        }
