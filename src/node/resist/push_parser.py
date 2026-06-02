from dspy import Predict, Prediction

from src.core.mechanic.threat_envelope import describe_threat
from src.core.model.resist import ResistAction
from src.lm import lm
from src.signature.resist_push_parser import ResistPushParserSignature
from src.state import GraphState


class ResistPushParserNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ResistPushParserSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        consequence = describe_threat(state.current_threat)
        prediction: Prediction = await self._program.aforward(
            consequence=consequence,
            player_response=state.resist_response or "",
        )
        # Push is retained mechanically but dropped from the offer surface
        # (no effect-on-target to spend it on yet) — fold it into resist.
        action = prediction.action
        if action == ResistAction.PUSH:
            action = ResistAction.RESIST
        return {"resist_action": action, "resist_flavor": prediction.flavor}