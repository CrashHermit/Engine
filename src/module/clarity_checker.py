from typing import AsyncGenerator
import dspy
from langchain_core.messages import (
    HumanMessage,
    BaseMessage,
    SystemMessage,
)


class ClarityCheckerSignature(dspy.Signature):
    """
    You are a clarity checker, you will take the input from the human and the chat history and you will return the clarity of the message.
    """
    message_history: list[str] = dspy.InputField(default_factory=list, description="The chat history")
    clarity_history: list[str] = dspy.InputField(default_factory=list, description="Accumulated player responses")
    
    human_message: str = dspy.InputField(default=HumanMessage(content="", name=""), description="The message to predict")
    is_cleared: bool = dspy.OutputField(default=False, description="Whether the message is clear")


class ClarityCheckerModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.clarity_checker_prediction: dspy.ChainOfThought = dspy.ChainOfThought(signature=ClarityCheckerSignature)

    async def aforward(self, message_history: list[BaseMessage], clarity_history: list[BaseMessage], human_message: HumanMessage) -> bool:
        message_history_str: list[str] = [f"{m.name}: {m.content}" for m in message_history]
        clarity_history_str: list[str] = [f"{m.name}: {m.content}" for m in clarity_history]
        human_message_str: str = f"{human_message.name}: {human_message.content}"

        prediction: dspy.Prediction = await self.clarity_checker_prediction.acall(
            message_history=message_history_str, clarity_history=clarity_history_str, human_message=human_message_str
        )
        return prediction.is_cleared

class ClarityChecker:
    def __init__(self) -> None:
        self.module: ClarityCheckerModule = ClarityCheckerModule()
    
    async def __call__(self, message_history: list[BaseMessage], clarity_history: list[BaseMessage], human_message: HumanMessage) -> bool:
        is_cleared: bool = await self.module.aforward(message_history, clarity_history, human_message)
        return is_cleared

    async def stream(
            self, 
            message_history: list[BaseMessage], 
            clarity_history: list[BaseMessage], 
            human_message: HumanMessage
        ) -> AsyncGenerator[bool | str, None]:
        streaming_engine: dspy.Streamify = dspy.streamify(
            program=self.module,
            stream_listeners=[dspy.streaming.StreamListener(signature_field_name="is_cleared")],
            is_async_program=True,
        )

        raw_stream: AsyncGenerator[bool | str, None] = streaming_engine(
            message_history=message_history,
            clarity_history=clarity_history,
            human_message=human_message
        )

        async for chunk in raw_stream:
            yield chunk
        
        final_is_cleared: bool | None = None

        async for chunk in raw_stream:
            if isinstance(chunk, bool):
                final_is_cleared: bool = chunk
            else:
                yield chunk
        
        if final_is_cleared is not None:
            yield final_is_cleared