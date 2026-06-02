from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.model.message import Message
from src.lm import lm
from src.state import GraphState


class NarratorSignature(Signature):
    """
    You are the narrator of a dark fantasy game in the spirit of Blades in
    the Dark. The world is dangerous, lived-in, and morally grey. Write in
    second person ("you"). Convey atmosphere, texture, and consequence.
    Let silence and small details do work. Never break immersion.

    Follow the provided narration_directive exactly — it tells you what to
    narrate this beat and any specific constraints (what to leave open,
    what to commit to, how to close). Use the provided anchors verbatim.
    Maintain the voice and rhythm of any prior_prose in context.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    message_history: str = InputField(default="")

    contested_beat: str = InputField(default="")
    narration_directive: str = InputField(
        description="What to narrate this turn, with any constraints"
    )
    anchors: str = InputField(
        default="", description="Sensory facts to include verbatim, newline-separated"
    )
    prior_prose: str = InputField(
        default="", description="Prose to continue from (empty for fresh starts)"
    )

    ai_message: str = OutputField()


class NarratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=NarratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        history = "\n".join(m.format() for m in state.message_history)
        entities = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        directive = state.narration_directive or ""
        # A creature changing posture this turn (noticing, turning hostile, or a
        # neutralized foe re-engaging) is narrated first, then the effect outcome.
        if state.engagement_note:
            directive = f"{directive}\n\nCreature posture change this turn: {state.engagement_note}"
        # The effect-on-target outcome (kill / disarm / rout / evade …) is a
        # structural instruction so prose can't recast a rout as a kill.
        if state.resolution_outcome:
            directive = f"{directive}\n\nResolution of the action on its target: {state.resolution_outcome}"
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=history,
            contested_beat=state.contested_beat or "",
            narration_directive=directive,
            anchors=state.anchors or "",
            prior_prose=state.prior_prose or "",
        )
        text = prediction.ai_message.strip()
        ai_message = Message(role="ai", content=text, name="Narrator")
        return {
            "ai_message": ai_message,
            "prior_prose": text,
        }
