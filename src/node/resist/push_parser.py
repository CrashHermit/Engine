from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.mechanic.threat_envelope import describe_threat
from src.core.model.resist import ResistAction
from src.lm import lm
from src.state import GraphState, current_threat


class ResistPushParserSignature(Signature):
    """Parse the player's response to a consequence offer.

    The player has seen a consequence and typed a response. Parse their intent:

    - resist: they want to reduce the consequence by one magnitude step. They
      are spending stress to push back against what happened.
    - push: they accept the consequence but want to spend stress to gain more
      effect from the action — the cost stands but the achievement is greater.
    - endure: they accept the consequence as-is, spending no stress.

    Read the player's response literally. If they describe resisting, bracing,
    deflecting, or pushing back → resist. If they describe pressing on, using
    the moment, or driving for more → push. If they accept, endure, or say
    nothing meaningful → endure.
    """

    consequence: str = InputField(
        description="What consequence landed (type, magnitude, channel)"
    )
    player_response: str = InputField(
        description="The player's typed response to the consequence offer"
    )

    action: ResistAction = OutputField(description="What the player chooses to do")
    flavor: str = OutputField(
        description=(
            "The player's described approach in one short sentence, or empty if endure"
        )
    )


class ResistPushParserNode:
    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ResistPushParserSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        consequence = describe_threat(current_threat(state))
        prediction: Prediction = await self._program.aforward(
            consequence=consequence,
            player_response=state.get("resist_response") or "",
        )
        # Push is retained mechanically but dropped from the offer surface
        # (no effect-on-target to spend it on yet) — fold it into resist.
        action = prediction.action
        if action == ResistAction.PUSH:
            action = ResistAction.RESIST
        return {"resist_action": action, "resist_flavor": prediction.flavor}
