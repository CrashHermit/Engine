from dspy import InputField, OutputField, Signature

from src.core.model.resist import HeldScaffold


class HeldPlannerSignature(Signature):
    """
    A consequence has landed (Minor, Standard, Severe, or Fatal). Extract
    a structured scaffold so the narrator can commit to the impact while
    deliberately leaving its depth and finality unresolved — the player may
    still resist or push.

    - impact_focus: the core of what the threat strikes (body part, memory,
      relationship, resource, position). One short phrase.
    - sensory_anchors: 2–3 concrete sensory details to ground the prose in the
      moment (sound, sensation, image). Keep them immediate and specific.
    - ambiguity_wedge: 2–3 dimensions to leave unresolved — severity,
      permanence, the exact extent of damage. Each as a short phrase the
      narrator must NOT commit to.
    - tension_close: one sentence describing how to end the beat — a breath
      of space, a held moment, an open question.
    - resist_options_text: 2–3 ways the character could plausibly resist or
      push back in the fiction. One sentence, suitable as the resist offer
      presented after the prose.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that was rolled"
    )
    threat_type: str = InputField(description="The kind of consequence that landed")
    threat_channel: str = InputField(description="The channel the consequence falls on")
    landed_magnitude: str = InputField(
        description="How severe the consequence is: MINOR, STANDARD, SEVERE, or FATAL"
    )

    scaffold: HeldScaffold = OutputField(
        description="Structured scaffold for the held narration"
    )
