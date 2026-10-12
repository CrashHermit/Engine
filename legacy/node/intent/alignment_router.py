from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.lm import lm
from src.state import GraphState


class IntentAlignmentRouterSignature(Signature):
    """You are an intent alignment router.

    Determine whether the player's message expresses clear, actionable intent
    given the current context and any prior intent alignment exchanges. Return
    true only when you have enough information to act. Return false if the
    intent is ambiguous, physically impossible for this character, contradicts
    the current context, or references an entity that does not exist in the
    current location.
    """

    message_history: str = InputField(
        default="", description="The conversation history so far"
    )
    human_message: str = InputField(
        description="The player's current message or action"
    )
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
        return {
            "is_intent_alignment_achieved": prediction.is_intent_alignment_achieved,
        }
