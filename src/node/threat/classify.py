from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.threat_envelope import magnitude_cap_for
from src.core.mechanic.threat_envelope import snap_channel
from src.core.model.entity import Danger
from src.core.model.threat import Threat

from src.core.model.location import EntityData
from src.core.mechanic.threat_envelope import position_for

from dspy import Predict, Prediction

from src.signature.threat_classifier import ThreatClassifierSignature
from src.lm import lm
from src.state import GraphState


class ClassifyThreatNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ThreatClassifierSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entity: EntityData | None = state.classify_entity
        source: str = state.classify_source or "environment"
        danger: Danger | None = entity.danger if entity is not None else None
        affinity = entity.threat_channels if entity is not None else frozenset()

        prediction: Prediction = await self._program.aforward(
            source=source,
            danger=danger.value if danger is not None else "environment",
            affinity=",".join(c.value for c in sorted(affinity)),
            character_description=state.character_description,
            location_description=state.location_description,
            contested_beat=state.contested_beat or "",
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