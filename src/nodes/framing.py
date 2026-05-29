"""The framing fan-out: five mutually-independent single-judgment classifiers
that run in parallel off the scoped beat (decisions #5, #18).

Each node writes a **disjoint** set of `GraphState` keys, so the concurrent
parallel edges never collide on a write (no reducer needed). They replace the
Phase-1 hardcoded framing stub in `ResolutionNode`; with the real `attribute`,
`threat_channel`, and `base_magnitude` in state, the resolution node now reads
its inputs from state instead of stubbing them.
"""

from dspy import Predict
from dspy.primitives.prediction import Prediction

from src.core.mechanics.magnitude import clamp_magnitude
from src.core.model.resolution import Attribute, Effect, ThreatType
from src.lm import lm
from src.signatures.attribute_selector import AttributeSelectorSignature
from src.signatures.effect_classifier import EffectClassifierSignature
from src.signatures.threat_channel_classifier import ThreatChannelClassifierSignature
from src.signatures.threat_magnitude_classifier import ThreatMagnitudeClassifierSignature
from src.signatures.threat_type_classifier import ThreatTypeClassifierSignature
from src.state import GraphState


def _entities(state: GraphState) -> str:
    return "\n".join(state.entities_at_location) if state.entities_at_location else ""


class AttributeSelectorNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=AttributeSelectorSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            contested_beat=state.contested_beat,
        )
        return {"attribute": Attribute(prediction.attribute).value}


class EffectClassifierNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=EffectClassifierSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=_entities(state),
            contested_beat=state.contested_beat,
        )
        return {"effect": Effect(prediction.effect).value}


class ThreatTypeClassifierNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ThreatTypeClassifierSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=_entities(state),
            contested_beat=state.contested_beat,
        )
        return {"threat_type": ThreatType(prediction.threat_type).value}


class ThreatMagnitudeClassifierNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ThreatMagnitudeClassifierSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=_entities(state),
            contested_beat=state.contested_beat,
        )
        # Threats run 1-4 (0 = "no threat" is the gate's job, not a magnitude).
        magnitude = clamp_magnitude(int(prediction.magnitude))
        return {"base_magnitude": max(1, magnitude)}


class ThreatChannelClassifierNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ThreatChannelClassifierSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            location_description=state.location_description,
            entities_at_location=_entities(state),
            contested_beat=state.contested_beat,
        )
        return {"threat_channel": Attribute(prediction.channel).value}
