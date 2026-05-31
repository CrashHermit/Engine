from dspy import InputField, OutputField, Signature

from src.core.model.resist import ResistAction


class ResistPushParserSignature(Signature):
    """
    The player has seen a consequence and typed a response. Parse their intent:

    - resist: they want to reduce the consequence by one magnitude step. They
      are spending stress to push back against what happened.
    - push: they accept the consequence but want to spend stress to gain more
      effect from the action — the cost stands but the achievement is greater.
    - endure: they accept the consequence as-is, spending no stress.

    Read the player's response literally. If they describe resisting, bracing,
    deflecting, or pushing back → resist. If they describe pressing on, using
    the moment, or driving for more → push. If they accept, endure, or say
    nothing meaningful → endure.
    """

    consequence: str = InputField(
        description="What consequence landed (type, magnitude, channel)"
    )
    player_response: str = InputField(
        description="The player's typed response to the consequence offer"
    )

    action: ResistAction = OutputField(
        description="What the player chooses to do"
    )
    flavor: str = OutputField(
        description="The player's described approach in one short sentence, or empty if endure"
    )
