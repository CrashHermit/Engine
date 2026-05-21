from typing import AsyncGenerator

import dspy

from core.model.message import Message
from module.utils import format_messages


class QuestionGeneratorSignature(dspy.Signature):
    """Generate a single clarifying DM-style question for ambiguous player input."""

    message_history: str = dspy.InputField(default="", description="The chat history")
    clarity_history: str = dspy.InputField(default="", description="Accumulated player responses")
    human_message: str = dspy.InputField(default="", description="The message to clarify")
    question: str = dspy.OutputField(description="A single focused clarifying question.")


class QuestionGeneratorModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.question_prediction = dspy.ChainOfThought(signature=QuestionGeneratorSignature)

    async def aforward(
        self,
        message_history: list[Message],
        clarity_history: list[Message],
        human_message: Message,
    ) -> str:
        prediction = await self.question_prediction.acall(
            message_history=format_messages(message_history),
            clarity_history=format_messages(clarity_history),
            human_message=format_messages([human_message]),
        )
        return prediction.question

    async def stream(
        self,
        message_history: list[Message],
        clarity_history: list[Message],
        human_message: Message,
    ) -> AsyncGenerator[str | dspy.Prediction, None]:
        streaming_engine = dspy.streamify(
            program=self,
            stream_listeners=[dspy.streaming.StreamListener(signature_field_name="question")],
            is_async_program=True,
        )
        async for chunk in streaming_engine(
            message_history=format_messages(message_history),
            clarity_history=format_messages(clarity_history),
            human_message=format_messages([human_message]),
        ):
            yield chunk
