from typing import AsyncGenerator

import dspy

from core.model.message import Message
from module.utils import format_messages


class ClarityCheckerSignature(dspy.Signature):
    """Determine if player intent is clear enough to proceed."""

    message_history: str = dspy.InputField(default="", description="The chat history")
    clarity_history: str = dspy.InputField(default="", description="Accumulated player responses")
    human_message: str = dspy.InputField(default="", description="The message to predict")
    is_cleared: str = dspy.OutputField(description="Whether the message is clear. Return exactly True or False with reasoning.")


class ClarityCheckerModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.clarity_checker_prediction = dspy.ChainOfThought(signature=ClarityCheckerSignature)

    async def aforward(
        self,
        message_history: list[Message],
        clarity_history: list[Message],
        human_message: Message,
    ) -> str:
        prediction = await self.clarity_checker_prediction.acall(
            message_history=format_messages(message_history),
            clarity_history=format_messages(clarity_history),
            human_message=format_messages([human_message]),
        )
        return prediction.is_cleared

    async def stream(
        self,
        message_history: list[Message],
        clarity_history: list[Message],
        human_message: Message,
    ) -> AsyncGenerator[str | dspy.Prediction, None]:
        streaming_engine = dspy.streamify(
            program=self,
            stream_listeners=[dspy.streaming.StreamListener(signature_field_name="is_cleared")],
            is_async_program=True,
        )
        async for chunk in streaming_engine(
            message_history=format_messages(message_history),
            clarity_history=format_messages(clarity_history),
            human_message=format_messages([human_message]),
        ):
            yield chunk


class ClarityChecker:
    def __init__(self) -> None:
        self.module: ClarityCheckerModule = ClarityCheckerModule()

    async def __call__(
        self,
        message_history: list[Message],
        clarity_history: list[Message],
        human_message: Message,
    ) -> bool:
        raw_result = await self.module.aforward(message_history, clarity_history, human_message)
        return "true" in raw_result.strip().lower()

    async def stream(
        self,
        message_history: list[Message],
        clarity_history: list[Message],
        human_message: Message,
    ) -> AsyncGenerator[str | bool, None]:
        final_prediction = None
        async for chunk in self.module.stream(message_history, clarity_history, human_message):
            if isinstance(chunk, dspy.Prediction):
                final_prediction = chunk
            else:
                yield chunk
        if final_prediction is not None:
            yield "true" in final_prediction.is_cleared.strip().lower()
