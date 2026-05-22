import dspy
from langgraph.config import get_stream_writer

from core.model.message import Message
from module.narrator import NarratorModule
from module.utils import format_messages
from state import GraphState

_module = NarratorModule()
_streaming_engine = dspy.streamify(
    program=_module,
    stream_listeners=[dspy.streaming.StreamListener(signature_field_name="ai_message", allow_reuse=True)],
    is_async_program=True,
)


async def narrator_node(state: GraphState) -> dict:
    writer = get_stream_writer()
    prediction: dspy.Prediction | None = None

    async for chunk in _streaming_engine(
        message_history=format_messages(state.message_history),
        human_message=state.human_message.content,
    ):
        if isinstance(chunk, dspy.streaming.StreamResponse):
            writer({"event": "token", "node": "narrator", "delta": chunk.chunk})
        elif isinstance(chunk, dspy.Prediction):
            prediction = chunk

    if prediction is None:
        raise RuntimeError("narrator stream ended without a prediction")

    writer({"event": "done", "node": "narrator", "content": prediction.ai_message.strip()})

    ai_message = Message(
        role="ai",
        content=prediction.ai_message.strip(),
        name="Narrator",
    )
    return {
        "message_history": [state.human_message, ai_message],
        "ai_message": ai_message,
    }
