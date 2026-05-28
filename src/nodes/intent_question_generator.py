from dspy import Predict
from dspy.primitives.prediction import Prediction
from src.lm import lm
from src.core.model.message import Message
from src.signatures.intent_question_generator import IntentQuestionGeneratorSignature
from src.state import GraphState


class IntentQuestionGeneratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=IntentQuestionGeneratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
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
        question_message = Message(role="ai", content=prediction.question, name="Intent Alignment")
        return {
            "intent_alignment_history": [state.human_message, question_message],
            "question": prediction.question,
        }
