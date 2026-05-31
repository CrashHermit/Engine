from dspy import Predict, Prediction

from src.core.mechanic.magnitude import Magnitude
from src.core.model.message import Message
from src.core.model.resist import HeldScaffold, ResistAction
from src.lm import lm
from src.signature.narrator import NarratorSignature
from src.state import GraphState


def _describe_outcome(state: GraphState) -> str:
    if state.outcome is None:
        return ""
    if state.outcome.crit:
        return "critical success — threat avoided; a benefit follows"
    if state.outcome.avoided:
        return "success — threat avoided"
    m = state.outcome.landed_magnitude
    if m == 0:
        return "threat reduced to nothing"
    mag = Magnitude(m).name.capitalize()
    ttype = state.threat_type.value if state.threat_type else "consequence"
    chan = f"({state.threat_channel.value})" if state.threat_channel else ""
    return f"{mag} {ttype} {chan} landed"


def _describe_final_outcome(state: GraphState) -> str:
    m = state.outcome.landed_magnitude if state.outcome else 0
    action = state.resist_action
    mag = Magnitude(m).name.capitalize() if m > 0 else "none"
    if action == ResistAction.RESIST:
        return f"resisted — consequence reduced to {mag}"
    if action == ResistAction.PUSH:
        return f"pushed for effect — {mag} consequence stands, greater effect achieved"
    return f"endured — {mag} consequence stands"


def _format_scaffold(scaffold: HeldScaffold) -> str:
    return (
        f"impact_focus: {scaffold.impact_focus}\n"
        f"sensory_anchors: {scaffold.sensory_anchors}\n"
        f"ambiguity_wedge: {scaffold.ambiguity_wedge}\n"
        f"tension_close: {scaffold.tension_close}\n"
        f"resist_options: {scaffold.resist_options}"
    )


class NarratorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=NarratorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entities = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        base = dict(
            character_name=state.character_name,
            character_description=state.character_description,
            location_name=state.location_name,
            location_description=state.location_description,
            entities_at_location=entities,
        )

        if state.held_narration is not None:
            # Final mode: resistance has resolved, continue from held prose.
            prediction: Prediction = await self._program.aforward(
                **base,
                prior_narration=state.held_narration,
                resist_resolution=state.resist_flavor or "",
                outcome=_describe_final_outcome(state),
            )
            ai_message = Message(
                role="ai", content=prediction.ai_message.strip(), name="Narrator"
            )
            return {
                "ai_message": ai_message,
                "message_history": [state.human_message, ai_message],
            }

        if state.held_scaffold is not None:
            # Held mode: consequence landed, resistance still pending.
            prediction = await self._program.aforward(
                **base,
                lead_up=state.lead_up or "",
                contested_beat=state.contested_beat or "",
                outcome=_describe_outcome(state),
                held_scaffold=_format_scaffold(state.held_scaffold),
            )
            held_text = prediction.ai_message.strip()
            ai_message = Message(role="ai", content=held_text, name="Narrator")
            return {
                "ai_message": ai_message,
                "held_narration": held_text,
                # message_history updated only after the full turn resolves
            }

        # Normal mode: no consequence or avoided.
        prediction = await self._program.aforward(
            **base,
            lead_up=state.lead_up or "",
            contested_beat=state.contested_beat or "",
            outcome=_describe_outcome(state),
        )
        ai_message = Message(
            role="ai", content=prediction.ai_message.strip(), name="Narrator"
        )
        return {
            "ai_message": ai_message,
            "message_history": [state.human_message, ai_message],
        }
