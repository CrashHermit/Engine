from typing import TYPE_CHECKING

from dspy import Predict

from src.lm import lm
from src.signatures.action_generator import ActionGeneratorSignature
from src.state import GraphState

if TYPE_CHECKING:
    from dspy.primitives.prediction import Prediction


class ActionGeneratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ActionGeneratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        message_history: str = "\n".join(m.format() for m in state.message_history)
        entities: str = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        prediction: Prediction = await self._program.aforward(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=message_history,
            human_message=state.human_message.content,
        )
        return {"action_list": prediction.action_list}
