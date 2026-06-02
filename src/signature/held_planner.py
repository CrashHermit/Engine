from dspy import InputField, OutputField, Signature

from src.core.model.resist import HeldScaffold


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