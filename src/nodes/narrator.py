import dspy
from dspy import ChainOfThought, Prediction
from dspy.streaming import StreamListener, StreamResponse
from langgraph.config import get_stream_writer

from core.model.message import Message
from signatures.narrator import NarratorSignature
from state import GraphState


def _format_history(messages: list[Message]) -> str:
    lines = []
    for msg in messages:
        label = msg.name if msg.name else msg.role.capitalize()
        lines.append(f"{label}: {msg.content}")
    return "\n".join(lines)


class NarratorNode:
    def __init__(self) -> None:
        self._stream = dspy.streamify(
            program=ChainOfThought(NarratorSignature),
            stream_listeners=[StreamListener(signature_field_name="ai_message")],
            is_async_program=True,
        )

    async def __call__(self, state: GraphState) -> dict:
        writer = get_stream_writer()
        prediction: Prediction | None = None

        async for chunk in self._stream(
            message_history=_format_history(state.message_history),
            human_message=state.human_message.content,
        ):
            if isinstance(chunk, StreamResponse):
                writer({"event": "token", "delta": chunk.chunk})
            elif isinstance(chunk, Prediction):
                prediction = chunk
                writer({"event": "message", "content": chunk.ai_message.strip()})

        if prediction is None:
            raise RuntimeError("NarratorNode stream ended without a prediction")

        ai_message = Message(
            role="ai",
            content=prediction.ai_message.strip(),
            name="Narrator",
        )
        return {
            "message_history": [state.human_message, ai_message],
            "ai_message": ai_message,
        }
