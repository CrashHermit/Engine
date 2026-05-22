from dspy import Predict

from core.model.message import Message
from signatures.narrator import NarratorSignature
from state import GraphState

from lm import lm


class NarratorNode:
    def __init__(self) -> None:
        self._program = Predict(signature=NarratorSignature)
        self._program.predict.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction = await self._program.aforward(
            human_message=state.human_message.content,
        )

        ai_message = Message(
            role="ai",
            content=prediction.ai_message.strip(),
            name="Narrator",
        )
        return {"ai_message": ai_message}
