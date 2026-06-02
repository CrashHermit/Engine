from dspy import Predict, Prediction

from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.narration_directive import held_directive
from src.core.model.resist import HeldScaffold
from src.lm import lm
from src.signature.held_planner import HeldPlannerSignature
from src.state import GraphState


class HeldPlannerNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=HeldPlannerSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entities = "\n".join(state.entities_at_location) if state.entities_at_location else ""
        landed = state.landed_threats
        consequences = "\n".join(
            f"{Magnitude(t.outcome.landed_magnitude).name} {t.type.value} "
            f"({t.channel.value}) from the {t.source}"
            for t in landed
        )

        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=entities,
            contested_beat=state.contested_beat or "",
            consequences=consequences,
        )
        scaffold: HeldScaffold = prediction.scaffold
        return {
            "held_scaffold": scaffold,
            "narration_directive": held_directive(scaffold),
            "anchors": "\n".join(scaffold.sensory_anchors),
            # Stable iteration order for the resist cycle.
            "resist_queue": [t.id for t in landed],
            "resist_cursor": 0,
        }