from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.model.message import Message
from src.lm import lm
from src.state import GraphState


class IntentQuestionGeneratorSignature(Signature):
    """You are an intent question generator for a text adventure game.

    The player's message is ambiguous or unclear. Ask one focused question to
    resolve the most important unknown. Take into account the character's
    abilities, location, entities present, and prior clarification exchanges.
    If the player references an entity that does not exist in the current
    location, inform them and suggest what is actually present. If the player
    is attempting something their character cannot reasonably do, explain why
    and ask them to reconsider. Ask only one question at a time with a brief
    explanation of why you need it.
    """

    character_name: str = InputField(
        default="", description="The player character's name"
    )
    location_name: str = InputField(
        default="", description="The name of the current location"
    )
    entity_names: str = InputField(
        default="",
        description="Names of entities present in the current location, one per line",
    )
    message_history: str = InputField(
        default="", description="The conversation history so far"
    )
    human_message: str = InputField(
        description="The player's current message or action"
    )
    intent_alignment_history: str = InputField(
        default="", description="The prior clarification Q&A for this action"
    )

    question: str = OutputField(
        description="One clarification question to ask the player"
    )


class IntentQuestionGeneratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=IntentQuestionGeneratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        message_history: str = "\n".join(
            m.format() for m in state.get("message_history", [])
        )
        intent_alignment_history: str = "\n".join(
            m.format() for m in state.get("intent_alignment_history", [])
        )
        entity_names = "\n".join(e.name for e in state.get("scene_entities", []))
        prediction: Prediction = await self._program.aforward(
            character_name=state.get("character_name", ""),
            location_name=state.get("location_name", ""),
            entity_names=entity_names,
            message_history=message_history,
            human_message=state.get("human_message").content,
            intent_alignment_history=intent_alignment_history,
        )
        question_message = Message(
            role="ai", content=prediction.question, name="Intent Alignment"
        )
        return {
            "intent_alignment_history": [question_message],
            "question": prediction.question,
        }
