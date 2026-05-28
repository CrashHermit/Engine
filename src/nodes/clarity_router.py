from dspy import Predict
from dspy.primitives.prediction import Prediction
from src.lm import lm
from src.signatures.clarity_router import ClarityRouterSignature
from src.state import GraphState


class ClarityRouterNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ClarityRouterSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        message_history: str = "\n".join(m.format() for m in state.message_history)
        clarity_history: str = "\n".join(m.format() for m in state.clarity_history)
        prediction: Prediction = await self._program.aforward(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            message_history=message_history,
            human_message=state.human_message.content,
            clarity_history=clarity_history,
        )
        return {
            "clarity_history": [state.human_message, prediction.question],
            "question": prediction.question,
            "is_clarity_achieved": prediction.is_clarity_achieved,
        }