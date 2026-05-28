from dspy.primitives.prediction import Prediction
from dspy import Predict

from src.core.model.message import Message
from src.signatures.narrator import NarratorSignature
from src.state import GraphState
from src.lm import lm


class NarratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=NarratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            message_history=state.message_history,
            human_message=state.human_message.content,
        )

        ai_message = Message(
            role="ai",
            content=prediction.ai_message.strip(),
            name="Narrator",
        )
        return {
            "message_history": [state.human_message, ai_message],
            "ai_message": ai_message,
        }
