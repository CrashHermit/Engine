from dspy import InputField, OutputField, Signature

from src.core.model.threat import Channel


class AttributeSelectorSignature(Signature):
    """
    You are an attribute selector. Given the contested beat the player is about
    to roll, decide which of the three attributes they should roll:

    - CORPUS: physical/material self — body, sensation, motor capacity.
      Climbing, lifting, dodging, stealth, striking, enduring physical strain.
    - MENS: interior cognition — thoughts, perceptions, memories, focus, reasoning.
      Recalling lore, spotting a lie, deducing a clue, sustaining attention,
      reading cues.
    - ANIMA: existential / relational self — identity, presence, bonds, oaths,
      essence. Persuading, leading, intimidating-by-presence, holding an oath,
      anchoring fate, performing.

    Pick the attribute that best matches what the player is actually *doing*
    in the contested beat — not what the threat resists with (that's a
    different classifier).
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    attribute: Channel = OutputField(
        description="Which attribute the player rolls for this beat"
    )