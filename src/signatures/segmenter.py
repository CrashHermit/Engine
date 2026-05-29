from dspy import InputField, OutputField, Signature


class SegmenterSignature(Signature):
    """
    Split the player's action into three parts around the FIRST beat that carries
    danger and uncertainty (the one that will be rolled). Runs only after the
    roll-gate has already decided a roll is needed (decision #9).

      - lead_up: mundane, safe setup that happens before the contested beat
                 (may be empty). Narrated freely, never rolled.
      - contested_beat: the single action that is actually attempted and rolled.
                 Exactly one beat — the first point where it could go wrong.
      - deferred_tail: everything the player stated AFTER that beat (may be empty).
                 Held for a later turn; never resolved now.

    Example: "cross the courtyard, cut down the guard, then grab the crown"
      lead_up        = "cross the courtyard"
      contested_beat = "cut down the guard"
      deferred_tail  = "grab the crown"

    Do not invent content. Every word of the player's action belongs to exactly
    one part, in order.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    entities_at_location: str = InputField(default="", description="Entities present in the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's full stated action")

    lead_up: str = OutputField(description="Mundane setup before the contested beat (may be empty)")
    contested_beat: str = OutputField(description="The single action to roll — the first danger+uncertainty beat")
    deferred_tail: str = OutputField(description="Anything stated after the contested beat (may be empty)")
