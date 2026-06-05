from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.model.message import Message
from src.lm import lm
from src.state import GraphState


class IntentSynthesizerSignature(Signature):
    """
    You are an intent synthesizer. Given the player's original message and the
    clarification Q&A that followed, produce a single clear, complete statement
    of what the player intends to do. The synthesized message should read as if
    the player wrote it themselves — first person, concrete, and actionable.
    Incorporate all resolved details from the clarification exchanges.
    """

    character_description: str = InputField(
        default="", description="A description of the player character"
    )
    location_description: str = InputField(
        default="", description="A description of the current location"
    )
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's original message or action")
    intent_alignment_history: str = InputField(
        description="The clarification Q&A that resolved the player's intent"
    )

    synthesized_message: str = OutputField(
        description="A single clear statement of the player's full intent"
    )


class IntentSynthesizerNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=IntentSynthesizerSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        if not state.get("intent_alignment_history", []):
            return {"human_message": state.get("human_message")}

        message_history: str = "\n".join(m.format() for m in state.get("message_history", []))
        intent_alignment_history: str = "\n".join(
            m.format() for m in state.get("intent_alignment_history", [])
        )
        prediction: Prediction = await self._program.aforward(
            character_name=state.get("character_name", ""),
            character_description=state.get("character_description", ""),
            location_name=state.get("location_name", ""),
            location_description=state.get("location_description", ""),
            message_history=message_history,
            human_message=state.get("human_message").content,
            intent_alignment_history=intent_alignment_history,
        )
        synthesized = Message(
            role="human",
            content=prediction.synthesized_message,
            name=state.get("human_message").name,
        )
        return {"human_message": synthesized}
