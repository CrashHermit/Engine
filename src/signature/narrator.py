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

    Ground the prose in the consequence area — threat_type, threat_channel,
    and landed_magnitude describe what the action's consequence strikes, where
    it lands, and how severe it is. The player must be able to feel the
    consequence in the prose. The narration_directive remains authoritative
    about which dimensions to commit to and which to hold open: never resolve
    a dimension the directive tells you to leave unresolved, but do make the
    nature and weight of the consequence vivid and legible within those bounds.
    These consequence fields may be empty for mundane beats; ignore them then.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    message_history: str = InputField(default="")

    contested_beat: str = InputField(default="")
    threat_type: str = InputField(
        default="", description="The kind of consequence (harm, complication, etc.)"
    )
    threat_channel: str = InputField(
        default="", description="The channel the consequence falls on (corpus, mens, anima)"
    )
    landed_magnitude: str = InputField(
        default="", description="How severe the consequence is: MINOR, STANDARD, SEVERE, or FATAL"
    )
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
