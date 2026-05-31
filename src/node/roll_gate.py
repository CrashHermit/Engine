from dspy import Predict, Prediction
from src.lm import lm
from src.signature.roll_gate import RollGateSignature
from src.state import GraphState

class RollGateNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=RollGateSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        history: str = "\n".join(m.format() for m in state.message_history)
        entities: str = (
            "\n".join(state.entities_at_location) if state.entities_at_location else ""
        )
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=history,
            human_message=state.human_message.content,
        )
        return {"needs_roll": prediction.needs_roll}