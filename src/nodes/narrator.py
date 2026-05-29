from dspy import Predict
from dspy.primitives.prediction import Prediction

from src.core.model.message import Message
from src.lm import lm
from src.signatures.narrator import NarratorSignature
from src.state import GraphState

_MAGNITUDE_WORD = {0: "no", 1: "minor", 2: "standard", 3: "severe", 4: "fatal"}


def format_outcome(state: GraphState) -> str:
    """Turn the resolved roll into a plain-language summary for the narrator.

    Deterministic ("threat as landed", decision #15) — the narrator turns it into
    prose. Empty string when no roll happened (a mundane beat).
    """
    if not state.needs_roll:
        return ""
    if state.outcome_avoided:
        if state.outcome_crit:
            return "The action succeeds cleanly and the character gains an advantage; the threat never lands."
        return "The action succeeds and the threat is avoided."

    landed = state.landed_magnitude or 0
    if landed == 0:
        return "The action succeeds; the threat is reduced to nothing."
    word = _MAGNITUDE_WORD.get(landed, "standard")
    return (
        f"The action resolves, but a {word} {state.threat_type or 'consequence'} "
        f"lands (channel: {state.threat_channel or 'unknown'})."
    )


class NarratorNode:
    """The lone generative module, bounded by construction (decision #9): it only
    ever sees `lead_up + contested_beat + outcome + effect`, never the raw message
    or the deferred tail, so it cannot run ahead of the resolved beat.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=NarratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        history = "\n".join(m.format() for m in state.message_history)
        entities: str = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        contested_beat = state.contested_beat or (
            state.human_message.content if state.human_message else ""
        )
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            message_history=history,
            lead_up=state.lead_up,
            contested_beat=contested_beat,
            outcome=format_outcome(state),
            effect=state.effect,
        )

        ai_message = Message(
            role="ai",
            content=prediction.ai_message.strip(),
            name="Narrator",
        )
        return {
            "message_history": [state.human_message, ai_message],
            "ai_message": ai_message,
        }
