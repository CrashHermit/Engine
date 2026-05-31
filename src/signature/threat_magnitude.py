from dspy import InputField, OutputField, Signature

from src.core.mechanic.magnitude import Magnitude


class ThreatMagnitudeSignature(Signature):
    """
    You are a threat magnitude classifier. Given the contested beat, decide
    how severe the consequence would be if the action fully fails. Use the
    1–4 ladder:

    - MINOR (1): a graze, a setback, a small complication, embarrassment.
      Recoverable in-scene.
    - STANDARD (2): a real wound, a meaningful complication, a position drop.
      Sticks around the scene, won't end the run.
    - SEVERE (3): a crippling wound, a major reversal, a lasting condition.
      Reshapes the next several scenes.
    - FATAL (4): potentially-lethal, life-altering, existential. Could end
      the character or its run.

    Pick the severity the *fiction* implies if the player rolls badly and
    doesn't resist. Don't soften because the player is skilled; the dice +
    resist mechanic handles that downstream.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    magnitude: Magnitude = OutputField(
        description="Severity of the consequence on the 1–4 ladder"
    )