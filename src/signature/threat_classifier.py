from dspy import InputField, OutputField, Signature

from src.core.model.threat import Channel, ThreatMagnitudeLevel, ThreatType


class ThreatClassifierSignature(Signature):
    """
    You are classifying the threat a SINGLE source poses during one contested
    beat. The source is either a named entity present in the scene or the
    environment itself. Many sources may threaten at once; you judge only this
    one.

    First decide whether this source meaningfully threatens the character in
    THIS beat. A bystander, a calm ally, or irrelevant scenery does not — set
    threatens=false and the rest is ignored.

    If it does threaten, classify the consequence if the action fully fails and
    the source's threat lands unresisted:

    - threat_type: harm / complication / worse_position / lost_opportunity /
      failure_of_goal.
    - magnitude: MINOR / STANDARD / SEVERE / FATAL — the severity the fiction
      implies. (A structural cap keyed to the source's danger is applied
      downstream; pick the honest fiction severity regardless.)
    - channel: corpus / mens / anima — where the consequence lands. If the
      source has an affinity, prefer it.

    `danger` and `affinity` describe this source's nature; weigh them but do
    not exceed what the fiction supports.
    """

    source: str = InputField(description="The entity name, or 'environment'")
    danger: str = InputField(description="Source danger tier, or 'environment'")
    affinity: str = InputField(default="", description="Comma-separated channels this source favours")
    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    contested_beat: str = InputField(description="The single contested action that needs a roll")

    threatens: bool = OutputField(description="Whether this source threatens the character this beat")
    threat_type: ThreatType = OutputField(description="Kind of consequence if it lands")
    magnitude: ThreatMagnitudeLevel = OutputField(description="Severity on the 1–4 ladder")
    channel: Channel = OutputField(description="Channel the consequence falls on")