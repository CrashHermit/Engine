from dspy import Predict, Prediction

from src.lm import lm
from src.signature.threat_type import ThreatTypeSignature
from src.state import GraphState


class ThreatTypeNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ThreatTypeSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=state.entities_at_location,
            contested_beat=state.contested_beat,
        )
        return {"threat_type": prediction.threat_type}
