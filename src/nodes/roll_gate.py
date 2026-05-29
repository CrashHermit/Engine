from dspy import Predict
from dspy.primitives.prediction import Prediction

from src.lm import lm
from src.signatures.roll_gate import RollGateSignature
from src.state import GraphState


class RollGateNode:
    """Binary gate (decision #9, split from the segmenter per #18): does the beat
    carry danger + uncertainty? On gate=true the `segmenter` runs next and owns the
    {lead_up, contested_beat, deferred_tail} split; on gate=false we narrate the
    whole message directly, so the contested_beat is seeded to the full message.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=RollGateSignature)
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
        return {
            "needs_roll": bool(prediction.needs_roll),
            # No-roll path narrates the message as-is; the segmenter overwrites this
            # on the roll path.
            "contested_beat": state.human_message.content,
        }
