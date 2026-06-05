from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.mechanic.narration_directive import final_directive
from src.core.model.resist import FinalScaffold, ResistAction
from src.lm import lm
from src.state import GraphState


class FinalPlannerSignature(Signature):
    """Reached only when nothing landed (clean/crit, or every threat reduced to
    0 at scale time). Narrates the avoided beat."""

    contested_beat: str = InputField(description="The action that was rolled")
    threat_type: str = InputField(default="")
    threat_channel: str = InputField(default="")
    landed_magnitude: str = InputField(description="The landed magnitude")
    held_ambiguities: str = InputField(default="")
    resist_action: str = InputField(default="endure")
    resist_flavor: str = InputField(default="")
    scaffold: FinalScaffold = OutputField(description="The final scaffold")
    narration_directive: str = OutputField(description="The narration directive")
    anchors: str = OutputField(description="The anchors")

class FinalPlannerNode:
    """Reached only when nothing landed (clean/crit, or every threat reduced to
    0 at scale time). Narrates the avoided beat."""

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=FinalPlannerSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entities = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        first = state.threats[0] if state.threats else None

        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            contested_beat=state.contested_beat or "",
            threat_type=first.type.value if first else "",
            threat_channel=first.channel.value if first else "",
            landed_magnitude="NONE",
            held_ambiguities="",
            resist_action=ResistAction.ENDURE.value,
            resist_flavor="",
        )
        scaffold: FinalScaffold = prediction.scaffold
        return {
            "final_scaffold": scaffold,
            "narration_directive": final_directive(scaffold, ResistAction.ENDURE),
            "anchors": "\n".join(scaffold.new_anchors),
        }