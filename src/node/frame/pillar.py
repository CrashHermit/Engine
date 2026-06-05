from __future__ import annotations

from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.model.entity import ThreatPillar
from src.lm import lm
from src.state import GraphState


class PillarSignature(Signature):
    """Identify which pillar of the target's threat the contested action attacks.

    The pillar is the condition the player is trying to remove (any one
    neutralises a foe):

    - exists: destroy/kill it (cut it down, crush it, blow it up).
    - capable: take away its means (disarm, cripple, restrain, blind).
    - aware: drop out of its awareness (sneak, hide, distract, deceive).
    - in_reach: break contact (flee, slip past, bar the door, gain distance).
    - willing: break its will (intimidate, demoralize, persuade, bribe, befriend).

    Pick the pillar the action is *trying* to affect, read from the verb. Default
    to exists for a plain attack, or when the action targets no specific foe.
    """

    character_description: str = InputField(default="")
    location_description: str = InputField(default="")
    entities_at_location: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    pillar: ThreatPillar = OutputField(
        description="Which condition of the target the action attacks (default exists)"
    )


class PillarNode:
    """Reads the contested beat → which pillar the action attacks. One judgment.

    Read from the verb, so it needs no resolved target and can run in parallel
    with the target classifier.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=PillarSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        entities = (
            "\n".join(state.get("entities_at_location", []))
            if state.get("entities_at_location", [])
            else ""
        )
        prediction: Prediction = await self._program.aforward(
            character_description=state.get("character_description", ""),
            location_description=state.get("location_description", ""),
            entities_at_location=entities,
            contested_beat=state.get("contested_beat", ""),
        )
        return {"target_pillar": prediction.pillar}
