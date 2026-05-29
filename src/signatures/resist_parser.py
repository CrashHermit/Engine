from dspy import InputField, OutputField, Signature


class ResistParserSignature(Signature):
    """
    The previous turn ended with a consequence landing and an offer to resist it
    (or push for more, decision #11). Read the player's typed reply and decide
    whether they choose to resist/push.

    Resisting: any reply where the player tries to avoid, soften, shrug off, brace
    against, or push through the consequence — including describing HOW they do so
    ("I twist so it catches my pauldron"). Their flavor colors later narration.

    Not resisting: the player accepts the consequence, moves on, ignores the offer,
    or takes a new unrelated action.
    """

    consequence: str = InputField(description="The consequence that landed and was offered for resistance")
    player_reply: str = InputField(description="The player's typed reply to the resistance offer")

    is_resisting: bool = OutputField(description="True if the player chooses to resist or push against the consequence")
