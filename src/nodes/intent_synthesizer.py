from dspy import Predict
from dspy.primitives.prediction import Prediction
from src.lm import lm
from src.core.model.message import Message
from src.signatures.intent_synthesizer import IntentSynthesizerSignature
from src.state import GraphState


class IntentSynthesizerNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=IntentSynthesizerSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        if not state.intent_alignment_history:
            return {"human_message": state.human_message}

        message_history: str = "\n".join(m.format() for m in state.message_history)
        intent_alignment_history: str = "\n".join(m.format() for m in state.intent_alignment_history)
        prediction: Prediction = await self._program.aforward(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            message_history=message_history,
            human_message=state.human_message.content,
            intent_alignment_history=intent_alignment_history,
        )
        synthesized = Message(
            role="human",
            content=prediction.synthesized_message,
            name=state.human_message.name,
        )
        return {"human_message": synthesized}
