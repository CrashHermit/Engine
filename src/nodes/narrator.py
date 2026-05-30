from typing import TYPE_CHECKING

from dspy import Predict

from src.core.model.message import Message
from src.lm import lm
from src.signatures.narrator import NarratorSignature
from src.state import GraphState

if TYPE_CHECKING:
    from dspy.primitives.prediction import Prediction


class NarratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=NarratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        history = "\n".join(m.format() for m in state.message_history)
        action_list = "\n".join(f"{i + 1}. {a}" for i, a in enumerate(state.action_list))
        entities: str = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        prediction: Prediction = await self._program.aforward(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=history,
            human_message=state.human_message.content,
            action_list=action_list,
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
