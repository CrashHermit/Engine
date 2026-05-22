from dspy import Predict

from core.model.message import Message
from signatures.narrator import NarratorSignature
from state import GraphState

from lm import lm


def _format_history(messages: list[Message]) -> str:
    lines: list[str] = []
    for msg in messages:
        if msg.role == "human":
            label = msg.name if msg.name else "Player"
        else:
            label = msg.name if msg.name else "Narrator"
        lines.append(f"[{label}]: {msg.content}")
    return "\n".join(lines)


class NarratorNode:
    def __init__(self) -> None:
        self._program = Predict(signature=NarratorSignature)
        self._program.predict.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        prediction = await self._program.aforward(
            message_history=_format_history(state.message_history),
            human_message=state.human_message.content,
        )

        ai_message = Message(
            role="ai",
            content=prediction.ai_message.strip(),
            name="Narrator",
        )
        return {
            "message_history": [state.human_message, ai_message],
            "ai_message": ai_message,
        }
