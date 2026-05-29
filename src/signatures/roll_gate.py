from dspy import InputField, OutputField, Signature


class RollGateSignature(Signature):
    """
    Decide whether the player's intended action requires a dice roll.

    A roll is needed ONLY when the action carries BOTH:
      - danger: there is a real threat or cost if it goes wrong, and
      - uncertainty: the outcome is genuinely in doubt.

    If the action is mundane, safe, or its success is not in question, no roll is
    needed — the narrator simply resolves it. ("If there's no risk and no doubt,
    just say yes.")
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    entities_at_location: str = InputField(default="", description="Entities present in the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's intended action")

    needs_roll: bool = OutputField(description="True only if the action carries both danger and uncertainty")
