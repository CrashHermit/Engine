import dspy
from langgraph.config import get_stream_writer

from core.model.message import Message
from module.utils import format_messages
from state import GraphState


class _NarratorSignature(dspy.Signature):
    """
    You are a narrator. Given the chat history and the player's latest message,
    narrate what happens next in the second person.
    """

    message_history: str = dspy.InputField(default="", description="The chat history so far")
    human_message: str = dspy.InputField(description="The player's latest message")
    ai_message: str = dspy.OutputField(description="The narration of the player's action")


class _NarratorModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.predict = dspy.ChainOfThought(signature=_NarratorSignature)

    async def aforward(self, message_history: str, human_message: str) -> dspy.Prediction:
        return await self.predict.acall(
            message_history=message_history,
            human_message=human_message,
        )


_streaming_narrator = dspy.streamify(
    program=_NarratorModule(),
    stream_listeners=[dspy.streaming.StreamListener(signature_field_name="ai_message", allow_reuse=True)],
    is_async_program=True,
)


async def narrator_node(state: GraphState) -> dict:
    writer = get_stream_writer()
    prediction: dspy.Prediction | None = None

    async for chunk in _streaming_narrator(
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
