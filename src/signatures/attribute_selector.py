from dspy import InputField, OutputField, Signature

from src.core.model.resolution import Attribute


class AttributeSelectorSignature(Signature):
    """
    Choose which of the three broad attributes the contested beat draws on
    (decision #1):

      - corpus: body — physical force, endurance, speed, dexterity, brawling.
      - mens:   mind — reasoning, perception, recall, tinkering, study.
      - anima:  spirit — will, nerve, presence, social sway, instinct, the uncanny.

    Pick the single attribute that best fits HOW the character attempts the beat.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    contested_beat: str = InputField(description="The single action being attempted")

    attribute: Attribute = OutputField(description="corpus, mens, or anima")
