from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.model.message import Message
from src.lm import lm
from src.state import GraphState


class IntentQuestionGeneratorSignature(Signature):
    """
    You are an intent question generator for a text adventure game. The player's
    message is ambiguous or unclear. Ask one focused question to resolve the most
    important unknown. Take into account the character's abilities, location,
    entities present, and prior clarification exchanges. If the player references
    an entity that does not exist in the current location, inform them and suggest
    what is actually present. If the player is attempting something their character
    cannot reasonably do, explain why and ask them to reconsider.
    Ask only one question at a time with a brief explanation of why you need it.
    """

    character_description: str = InputField(
        default="", description="A description of the player character"
    )
    location_description: str = InputField(
        default="", description="A description of the current location"
    )
    entities_at_location: str = InputField(
        default="",
        description="Entities present in the current location, each formatted as 'Name: description. Location: scene_position'",
    )
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's current message or action")
    intent_alignment_history: str = InputField(
        default="", description="The prior clarification Q&A for this action"
    )

    question: str = OutputField(description="One clarification question to ask the player")


class IntentQuestionGeneratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=IntentQuestionGeneratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        message_history: str = "\n".join(m.format() for m in state.message_history)
        intent_alignment_history: str = "\n".join(
            m.format() for m in state.intent_alignment_history
        )
        entities: str = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        prediction: Prediction = await self._program.aforward(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=message_history,
            human_message=state.human_message.content,
            intent_alignment_history=intent_alignment_history,
        )
        question_message = Message(role="ai", content=prediction.question, name="Intent Alignment")
        return {
            "intent_alignment_history": [question_message],
            "question": prediction.question,
        }
