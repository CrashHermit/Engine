from __future__ import annotations

from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.mechanic.narration_directive import final_directive
from src.core.model.resist import FinalScaffold, ResistAction
from src.lm import lm
from src.state import GraphState


class FinalPlannerSignature(Signature):
    """A consequence is resolving.

    Produce a structured scaffold for the final narrator prose.

    - resolutions: list of "dimension: outcome" strings that collapse any
      ambiguities held open in the prior narration (e.g. "depth: shallow —
      the blow glanced off armour"). If there was no held phase, describe
      how the consequence landed in 1–2 short phrases.
    - new_anchors: 1–3 concrete sensory details for the resolution moment,
      distinct from anything already in the prior prose.
    - closing_beat: one sentence for how this beat ends — the character's
      immediate state, a held breath, what they now face.
    - incorporate_player_text: the player's resist or push framing rephrased
      as a short active sentence to weave into the prose. Empty string if
      the player endured.
    """

    contested_beat: str = InputField(description="The action that was rolled")
    threat_type: str = InputField(default="")
    threat_channel: str = InputField(default="")
    landed_magnitude: str = InputField(
        description=(
            "Final severity after any resistance:"
            " NONE, MINOR, STANDARD, SEVERE, or FATAL"
        )
    )
    held_ambiguities: str = InputField(
        default="",
        description=(
            "Dimensions left open in the held narration; empty if no held phase"
        ),
    )
    resist_action: str = InputField(
        default="endure",
        description="What the player chose: resist, push, or endure",
    )
    resist_flavor: str = InputField(
        default="",
        description="The player's own framing of their response; empty if enduring",
    )

    scaffold: FinalScaffold = OutputField(
        description="Structured scaffold for the final narration"
    )


class FinalPlannerNode:
    """Narrate the avoided beat when nothing landed.

    Reached only when nothing landed (clean/crit, or every threat reduced to
    0 at scale time).
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=FinalPlannerSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        first = state.get("threats", [])[0] if state.get("threats", []) else None

        prediction: Prediction = await self._program.aforward(
            contested_beat=state.get("contested_beat", "") or "",
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
