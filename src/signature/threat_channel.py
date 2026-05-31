from dspy import InputField, OutputField, Signature

from src.core.model.threat import Channel


class ThreatChannelSignature(Signature):
    """
    You are a threat channel classifier. Given the contested beat, decide
    which of the three channels the looming consequence would land on
    (and therefore which attribute can resist it):

    - CORPUS: physical consequence — wounds, exhaustion, restraint, poison,
      environmental damage.
    - MENS: cognitive consequence — confusion, paranoia, false memory,
      cognitive overload, distraction.
    - ANIMA: existential/relational consequence — broken bond, eroded
      presence, oath stress, identity damage, faded standing.

    This is independent of the attribute the player rolls. Climbing a wall
    rolls Corpus but the threat might be Mens (panic at the height) or
    Anima (the climb is sworn to a witness who is watching). Pick the
    channel the *consequence itself* lives on.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    channel: Channel = OutputField(
        description="Which channel the consequence falls on"
    )