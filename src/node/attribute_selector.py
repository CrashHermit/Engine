from dspy import Predict, Prediction

from src.lm import lm
from src.signature.attribute_selector import AttributeSelectorSignature
from src.state import GraphState


class AttributeSelectorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=AttributeSelectorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            contested_beat=state.contested_beat,
        )
        return {"attribute": prediction.attribute}