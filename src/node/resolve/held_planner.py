from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.narration_directive import held_directive
from src.core.model.resist import HeldScaffold
from src.lm import lm
from src.state import GraphState, landed_threats


class HeldPlannerSignature(Signature):
    """
    One or more consequences have landed at once. Produce a single COHESIVE
    scaffold so the narrator can set the whole moment as one blended beat —
    committing to each impact while leaving depth and finality unresolved (the
    player will resist each in turn).

    - impact_focus: the core of what was struck, across all listed
      consequences. One short phrase.
    - sensory_anchors: 2–3 concrete sensory details grounding the combined
      moment.
    - ambiguity_wedge: 2–3 dimensions to leave open (severity, permanence,
      extent) — the narrator must NOT commit to these.
    - tension_close: one sentence ending the beat on a held breath.
    - resist_options_text: not used as the per-threat offer (those are posed
      one at a time downstream); keep it a short line of in-fiction options.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(description="The single contested action that was rolled")
    consequences: str = InputField(
        description="The landed consequences, one per line: 'SEVERE harm (corpus) from the warden'"
    )

    scaffold: HeldScaffold = OutputField(description="Cohesive scaffold for the held narration")


class HeldPlannerNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=HeldPlannerSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entities = "\n".join(state.get("entities_at_location", [])) if state.get("entities_at_location", []) else ""
        landed = landed_threats(state)
        consequences = "\n".join(
            f"{Magnitude(t.outcome.landed_magnitude).name} {t.type.value} "
            f"({t.channel.value}) from the {t.source}"
            for t in landed
        )

        prediction: Prediction = await self._program.aforward(
            character_description=state.get("character_description", ""),
            location_description=state.get("location_description", ""),
            entities_at_location=entities,
            contested_beat=state.get("contested_beat", "") or "",
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