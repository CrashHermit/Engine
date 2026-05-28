from dspy import Predict
from dspy.primitives.prediction import Prediction
from src.lm import lm
from src.signatures.intent_alignment_router import IntentAlignmentRouterSignature
from src.state import GraphState


class IntentAlignmentRouterNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=IntentAlignmentRouterSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        message_history: str = "\n".join(m.format() for m in state.message_history)
        intent_alignment_history: str = "\n".join(m.format() for m in state.intent_alignment_history)
        entities: str = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        prediction: Prediction = await self._program.aforward(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=message_history,
            human_message=state.human_message.content,
            intent_alignment_history=intent_alignment_history,
        )
        return {
            "is_clarity_achieved": prediction.is_clarity_achieved,
        }
