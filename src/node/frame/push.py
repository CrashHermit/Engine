from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.lm import lm
from src.state import GraphState


class PushSignature(Signature):
    """
    Given the contested beat the player is about to roll, decide whether the
    player is PUSHING THEMSELVES — going all-out, throwing everything in, taking
    extra risk/exertion for a harder hit (e.g. "I put everything into one savage
    blow"). A normal, measured action is not a push. A push costs stress for
    extra effect, so only flag it when the player clearly reaches for more.
    """

    character_description: str = InputField(default="")
    contested_beat: str = InputField(
        description="The single contested action that needs a roll"
    )

    push: bool = OutputField(
        description="True only if the player is clearly pushing themselves for extra effect"
    )


class PushNode:
    """Reads the contested beat → whether the player pushes for effect. One bit."""

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=PushSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction: Prediction = await self._program.aforward(
            character_description=state.character_description,
            contested_beat=state.contested_beat,
        )
        return {"push_for_effect": bool(prediction.push)}
