from dspy import Predict, Prediction

from src.core.mechanic.magnitude import Magnitude
from src.lm import lm
from src.signature.resist_push_parser import ResistPushParserSignature
from src.state import GraphState


class ResistPushParserNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ResistPushParserSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        m = state.outcome.landed_magnitude if state.outcome else 0
        mag = Magnitude(m).name.capitalize() if m > 0 else "none"
        ttype = state.threat_type.value if state.threat_type else "consequence"
        chan = state.threat_channel.value if state.threat_channel else ""
        consequence = f"{mag} {ttype} ({chan})"

        prediction: Prediction = await self._program.aforward(
            consequence=consequence,
            player_response=state.resist_response or "",
        )
        return {
            "resist_action": prediction.action,
            "resist_flavor": prediction.flavor,
        }
