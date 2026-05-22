import logging

from dspy import (
    Prediction,
    Predict,
    streamify,
)
from dspy.streaming import (
    StreamListener,
    StreamResponse,
)
from langgraph.config import get_stream_writer

from core.model.message import Message
from signatures.narrator import NarratorSignature
from state import GraphState

from lm import lm

logger = logging.getLogger(__name__)

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
        program: Predict = Predict(signature=NarratorSignature)
        program.predict.lm = lm
        self._stream: streamify | None = streamify(
            program=program,
            stream_listeners=[StreamListener(signature_field_name="ai_message")],
            is_async_program=True,
        )

    async def __call__(self, state: GraphState) -> dict:
        writer = get_stream_writer()
        prediction: Prediction | None = None

        formatted_history = _format_history(state.message_history)
        logger.debug(
            "NarratorNode calling LLM | history_len=%d | history=%r | human_message=%r",
            len(state.message_history),
            formatted_history,
            state.human_message.content,
        )

        token_count = 0
        async for chunk in self._stream(
            message_history=formatted_history,
            human_message=state.human_message.content,
        ):
            logger.debug("DSPy chunk type=%s value=%r", type(chunk).__name__, chunk)
            if isinstance(chunk, StreamResponse):
                token_count += 1
                writer({"event": "token", "delta": chunk.chunk})
            elif isinstance(chunk, Prediction):
                prediction = chunk
                logger.debug(
                    "DSPy Prediction received | ai_message=%r", chunk.ai_message
                )
                writer({"event": "message", "content": chunk.ai_message.strip()})

        logger.info(
            "NarratorNode stream done | tokens_streamed=%d | got_prediction=%s",
            token_count,
            prediction is not None,
        )

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
