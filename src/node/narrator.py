from dspy import Predict, Prediction

from src.core.mechanic.magnitude import Magnitude
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
        mag = state.outcome.landed_magnitude if state.outcome else 0
        mag_label = Magnitude(mag).name if mag > 0 else ""
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=history,
            contested_beat=state.contested_beat or "",
            threat_type=state.threat_type.value if state.threat_type else "",
            threat_channel=state.threat_channel.value if state.threat_channel else "",
            landed_magnitude=mag_label,
            narration_directive=state.narration_directive or "",
            anchors=state.anchors or "",
            prior_prose=state.prior_prose or "",
        )
        text = prediction.ai_message.strip()
        ai_message = Message(role="ai", content=text, name="Narrator")
        return {
            "ai_message": ai_message,
            "prior_prose": text,
        }
