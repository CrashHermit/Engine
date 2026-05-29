from dspy import InputField, OutputField, Signature

from src.core.model.resolution import Effect


class EffectClassifierSignature(Signature):
    """
    Judge how much a success would accomplish within this single beat — the
    effect level (not whether it succeeds, only its reach if it does):

      - limited: a partial or hard-won result; the obstacle is tough, the tool
                 ill-suited, or the character impaired.
      - standard: a solid, expected result for a capable character.
      - great:   an outsized result; the character is well-matched, well-equipped,
                 or the obstacle is soft.

    Consider the character (including any impaired body parts), the target, and
    the situation. Default to standard when nothing pushes it either way.
    """

    character_description: str = InputField(default="", description="A description of the player character, including any wounded/impaired parts")
    location_description: str = InputField(default="", description="A description of the current location")
    entities_at_location: str = InputField(default="", description="Entities present in the current location")
    contested_beat: str = InputField(description="The single action being attempted")

    effect: Effect = OutputField(description="limited, standard, or great")
