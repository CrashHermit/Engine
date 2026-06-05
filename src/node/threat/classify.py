from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.threat_envelope import (
    magnitude_cap_for,
    position_for,
    snap_channel,
)
from src.core.model.entity import Danger
from src.core.model.location import EntityData
from src.core.model.threat import Channel, Threat, ThreatMagnitudeLevel, ThreatType
from src.lm import lm
from src.state import GraphState


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


class ClassifyThreatNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ThreatClassifierSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entity: EntityData | None = state.get("classify_entity")
        source: str = state.get("classify_source", "") or "environment"
        danger: Danger | None = entity.danger if entity is not None else None
        affinity = entity.threat_channels if entity is not None else frozenset()

        prediction: Prediction = await self._program.aforward(
            source=source,
            danger=danger.value if danger is not None else "environment",
            affinity=",".join(c.value for c in sorted(affinity)),
            character_description=state.get("character_description", ""),
            location_description=state.get("location_description", ""),
            contested_beat=state.get("contested_beat", "") or "",
        )
        if not prediction.threatens:
            return {}

        cap = magnitude_cap_for(danger)
        magnitude = min(Magnitude[prediction.magnitude], cap)
        channel = snap_channel(prediction.channel, affinity)
        threat = Threat(
            source=source,
            type=prediction.threat_type,
            channel=channel,
            magnitude=magnitude,
            position=position_for(danger),
        )
        return {"pending_threats": [threat]}
