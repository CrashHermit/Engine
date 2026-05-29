from dspy import InputField, OutputField, Signature

from src.core.model.resolution import ThreatType


class ThreatTypeClassifierSignature(Signature):
    """
    Name the KIND of threat that looms if the contested beat goes badly — fixed
    before the roll (decision #15). Pick exactly one:

      - harm: physical injury to the character's body.
      - complication: a new problem, entanglement, or cost in the fiction.
      - worse_position: the situation grows more dangerous / desperate.
      - lost_opportunity: a window closes; an advantage slips away.
      - failure_of_goal: the action simply doesn't achieve its aim.

    Choose the most fitting consequence for THIS beat. failure_of_goal is a normal,
    first-class outcome — not a fallback (decision #16). The fiction is written
    later by the narrator; you only name the type.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    entities_at_location: str = InputField(default="", description="Entities present in the current location")
    contested_beat: str = InputField(description="The single action being attempted")

    threat_type: ThreatType = OutputField(description="harm, complication, worse_position, lost_opportunity, or failure_of_goal")
