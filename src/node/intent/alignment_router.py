from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.lm import lm
from src.state import GraphState


class IntentAlignmentRouterSignature(Signature):
    """
    You are an intent alignment router. Determine whether the player's message
    expresses clear, actionable intent given the current context and any prior
    intent alignment exchanges. Return true only when you have enough information
    to act. Return false if the intent is ambiguous, physically impossible for
    this character, contradicts the current context, or references an entity
    that does not exist in the current location.
    """

    character_name: str = InputField(default="", description="The player character's name")
    character_description: str = InputField(
        default="", description="A description of the player character"
    )
    location_name: str = InputField(default="", description="The name of the current location")
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

    is_intent_alignment_achieved: bool = OutputField(
        description="Whether the player's intent is clear enough to act on"
    )


class IntentAlignmentRouterNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=IntentAlignmentRouterSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict[str, bool]:
        message_history: str = "\n".join(m.format() for m in state.get("message_history", []))
        intent_alignment_history: str = "\n".join(
            m.format() for m in state.get("intent_alignment_history", [])
        )
        entities: str = "\n".join(state.get("entities_at_location", [])) if state.get("entities_at_location", []) else ""
        prediction: Prediction = await self._program.aforward(
            character_name=state.get("character_name", ""),
            character_description=state.get("character_description", ""),
            location_name=state.get("location_name", ""),
            location_description=state.get("location_description", ""),
            entities_at_location=entities,
            message_history=message_history,
            human_message=state.get("human_message").content,
            intent_alignment_history=intent_alignment_history,
        )
        return {
            "is_intent_alignment_achieved": prediction.is_intent_alignment_achieved,
        }
