from dspy import Predict, Prediction

from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.narration_directive import final_directive
from src.core.model.resist import FinalScaffold, ResistAction
from src.lm import lm
from src.signature.final_planner import FinalPlannerSignature
from src.state import GraphState


class FinalPlannerNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=FinalPlannerSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entities = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        mag = state.outcome.landed_magnitude if state.outcome else 0
        mag_label = Magnitude(mag).name if mag > 0 else "NONE"

        held_ambiguities = (
            "\n".join(state.held_scaffold.ambiguity_wedge)
            if state.held_scaffold is not None
            else ""
        )
        resist_action = state.resist_action or ResistAction.ENDURE

        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            contested_beat=state.contested_beat or "",
            threat_type=state.threat_type.value if state.threat_type else "",
            threat_channel=state.threat_channel.value if state.threat_channel else "",
            landed_magnitude=mag_label,
            held_ambiguities=held_ambiguities,
            resist_action=resist_action.value,
            resist_flavor=state.resist_flavor or "",
        )
        scaffold: FinalScaffold = prediction.scaffold
        return {
            "final_scaffold": scaffold,
            "narration_directive": final_directive(scaffold, resist_action),
            "anchors": "\n".join(scaffold.new_anchors),
        }
