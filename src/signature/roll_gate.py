from dspy import InputField, OutputField, Signature


class RollGateSignature(Signature):
    """
    You are a roll gate. Decide whether the player's intent for this beat needs
    a dice roll. A roll is needed only when the action carries BOTH danger and
    uncertainty:

    - Danger: failure or partial success would meaningfully cost the character
      (harm, complication, lost opportunity, position degradation).
    - Uncertainty: the outcome is genuinely in doubt given the character's
      capability, the situation, and the fiction.

    Mundane intent that has neither (walking to an unguarded room, picking up
    an obvious item, speaking a line with no social stakes) does NOT need a
    roll. Narrate it directly.

    Return true only when both danger and uncertainty are clearly present.
    Return false otherwise.
    """

    character_description: str = InputField(
        default="", description="A description of the player character"
    )
    location_description: str = InputField(
        default="", description="A description of the current location"
    )
    entities_at_location: str = InputField(
        default="",
        description="Entities present in the current location, each formatted as 'Name: description. Location: scene_position'",
    )
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's intended action")

    needs_roll: bool = OutputField(
        description="Whether the beat needs a dice roll (true only when danger AND uncertainty are present)"
    )