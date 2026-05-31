from dspy import InputField, OutputField, Signature


class NarratorSignature(Signature):
    """
    You are the narrator of a dark fantasy game in the spirit of Blades in
    the Dark. The world is dangerous, lived-in, and morally grey. Write in
    second person ("you"). Convey atmosphere, texture, and consequence.
    Let silence and small details do work. Never break immersion.

    Follow the provided narration_directive exactly — it tells you what to
    narrate this beat and any specific constraints (what to leave open,
    what to commit to, how to close). Use the provided anchors verbatim.
    Maintain the voice and rhythm of any prior_prose in context.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    message_history: str = InputField(default="")

    contested_beat: str = InputField(default="")
    narration_directive: str = InputField(
        description="What to narrate this turn, with any constraints"
    )
    anchors: str = InputField(
        default="", description="Sensory facts to include verbatim, newline-separated"
    )
    prior_prose: str = InputField(
        default="", description="Prose to continue from (empty for fresh starts)"
    )

    ai_message: str = OutputField()
