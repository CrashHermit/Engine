from dspy import Predict
from dspy.primitives.prediction import Prediction

from src.lm import lm
from src.signatures.segmenter import SegmenterSignature
from src.state import GraphState


class SegmenterNode:
    """Split the message into {lead_up, contested_beat, deferred_tail} (decision
    #9). Runs only on the gate=true path; the tail is held, never sent downstream.
    Replaces the Phase-1 stub segmentation that lived in the roll-gate.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=SegmenterSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        message_history: str = "\n".join(m.format() for m in state.message_history)
        entities: str = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=message_history,
            human_message=state.human_message.content,
        )
        contested_beat = (prediction.contested_beat or "").strip()
        return {
            "lead_up": (prediction.lead_up or "").strip(),
            # Fall back to the whole message if the model returns an empty beat.
            "contested_beat": contested_beat or state.human_message.content,
            "deferred_tail": (prediction.deferred_tail or "").strip(),
        }
