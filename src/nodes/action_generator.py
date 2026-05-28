from dspy import Predict
from dspy.primitives.prediction import Prediction
from src.lm import lm
from src.signatures.action_generator import ActionGeneratorSignature
from src.state import GraphState


class ActionGeneratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ActionGeneratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        message_history: str = "\n".join(m.format() for m in state.message_history)
        prediction: Prediction = await self._program.aforward(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            message_history=message_history,
            human_message=state.human_message.content,
        )
        return {"action_list": prediction.action_list}
