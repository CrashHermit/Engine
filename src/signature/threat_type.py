from dspy import InputField, OutputField, Signature

from src.core.model.threat import ThreatType


class ThreatTypeSignature(Signature):
    """
    You are a threat type classifier. Given the contested beat, decide what
    kind of consequence the character faces if the action fully fails:

    - harm: direct damage to the character — wounds, exhaustion, poison,
      cognitive overload, psychic damage, erosion of presence or bonds.
    - complication: a new problem enters the fiction — an alarm raised, a
      witness, a dropped item, a worsened relationship, an unexpected obstacle.
    - worse_position: the character ends up in a more dangerous or constrained
      situation — cornered, exposed, on the back foot, out of cover.
    - lost_opportunity: a window closes — the target escapes, the contact
      leaves, the moment passes, the advantage evaporates.
    - failure_of_goal: the character simply doesn't accomplish the beat — the
      lock won't turn, the argument falls flat, the jump comes up short.

    Pick the type that best describes what goes wrong in the fiction. Harm is
    for direct damage; complication is for new problems; worse_position is for
    narrative positioning; lost_opportunity is for missed chances;
    failure_of_goal is when the action just doesn't work.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    threat_type: ThreatType = OutputField(
        description="The kind of consequence if the action fully fails"
    )
