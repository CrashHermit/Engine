from dspy import InputField, OutputField, Signature

from src.core.mechanics.magnitude import Magnitude


class ThreatMagnitudeClassifierSignature(Signature):
    """
    Judge how BAD the looming threat is if the beat goes wrong — its base
    magnitude on the shared 1–4 ladder, fixed before the roll (decision #15).
    Code scales this down by the roll result; you set the worst case.

      - 1 Minor:    a setback, a scrape, an annoyance.
      - 2 Standard: a real injury or solid problem.
      - 3 Severe:   a grave wound or serious reversal.
      - 4 Fatal:    potentially lethal / catastrophic.

    Weigh the danger in the fiction (the foe, the fall, the fire). Most everyday
    threats are Minor or Standard; reserve Fatal for the genuinely deadly.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    entities_at_location: str = InputField(default="", description="Entities present in the current location")
    contested_beat: str = InputField(description="The single action being attempted")

    magnitude: int = OutputField(description="Base threat magnitude: 1 Minor, 2 Standard, 3 Severe, or 4 Fatal")
