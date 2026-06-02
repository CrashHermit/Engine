from dspy import InputField, OutputField, Signature

from src.core.model.entity import ThreatPillar
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

    Also identify the target: the entity the action is directed at (the foe
    being struck, the lock being forced). Return its exact name from the listed
    entities, or an empty string if the action targets no specific entity.

    Finally, identify which *pillar* of the target's threat the action attacks —
    the condition the player is trying to remove (any one neutralises a foe):

    - exists: destroy/kill it (cut it down, crush it, blow it up).
    - capable: take away its means (disarm, cripple, restrain, blind).
    - aware: drop out of its awareness (sneak, hide, distract, deceive).
    - in_reach: break contact (flee, slip past, bar the door, gain distance).
    - willing: break its will (intimidate, demoralize, persuade, bribe, befriend).

    Pick the pillar the action is *trying* to affect. Default to exists for a
    plain attack; use exists too when no specific target.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    attribute: Channel = OutputField(
        description="Which attribute the player rolls for this beat"
    )
    target: str = OutputField(
        description=(
            "Exact name of the entity the action is directed at, or empty "
            "string if none (movement, perception, environment)."
        )
    )
    pillar: ThreatPillar = OutputField(
        description="Which condition of the target the action attacks (default exists)"
    )