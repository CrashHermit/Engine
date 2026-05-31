from dspy import InputField, OutputField, Signature

from src.core.model.resist import FinalScaffold


class FinalPlannerSignature(Signature):
    """
    A consequence is resolving. Produce a structured scaffold for the final
    narrator prose.

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

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(description="The action that was rolled")
    threat_type: str = InputField(default="")
    threat_channel: str = InputField(default="")
    landed_magnitude: str = InputField(
        description="Final severity after any resistance: NONE, MINOR, STANDARD, SEVERE, or FATAL"
    )
    held_ambiguities: str = InputField(
        default="",
        description="Dimensions left open in the held narration; empty if no held phase",
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
