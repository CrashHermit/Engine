from typing import AsyncGenerator, Union
import dspy
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage

# =====================================================================
# 1. DSPY SIGNATURE DEFINITION
# =====================================================================
class ClarityCheckerSignature(dspy.Signature):
    """You are a clarity checker, you will take the input from the human and the chat history 
    and you will return the clarity of the message."""
    
    message_history: list[str] = dspy.InputField(description="The chat history")
    clarity_history: list[str] = dspy.InputField(description="Accumulated player responses")
    human_message: str = dspy.InputField(description="The message to predict")
    # Kept as a string so DSPy can natively stream the generation tokens/reasoning
    is_cleared: str = dspy.OutputField(description="Whether the message is clear. Return exactly True or False with reasoning.")


# =====================================================================
# 2. DSPY CORE MODULE DEFINITION
# =====================================================================
class ClarityCheckerModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.clarity_checker_prediction = dspy.ChainOfThought(signature=ClarityCheckerSignature)

    async def aforward(self, message_history: list[BaseMessage], clarity_history: list[BaseMessage], human_message: HumanMessage) -> str:
        message_history_str = [f"{m.name}: {m.content}" for m in message_history]
        clarity_history_str = [f"{m.name}: {m.content}" for m in clarity_history]
        human_message_str = f"{human_message.name}: {human_message.content}"
        
        prediction = await self.clarity_checker_prediction.acall(
            message_history=message_history_str,
            clarity_history=clarity_history_str,
            human_message=human_message_str
        )
        return prediction.is_cleared

    async def stream(
        self, 
        message_history: list[BaseMessage], 
        clarity_history: list[BaseMessage], 
        human_message: HumanMessage
    ) -> AsyncGenerator[Union[str, dspy.Prediction], None]:
        
        # FIX 1: Point program to 'self' instead of a non-existent 'self.module'
        streaming_engine = dspy.streamify(
            program=self,
            stream_listeners=[dspy.streaming.StreamListener(signature_field_name="is_cleared")],
            is_async_program=True,
        )
        
        raw_stream = streaming_engine(
            message_history=message_history,
            clarity_history=clarity_history,
            human_message=human_message
        )

        # FIX 2: Consumed the stream using exactly ONE clean loop
        async for chunk in raw_stream:
            yield chunk


# =====================================================================
# 3. HIGH-LEVEL WRAPPER CLASS
# =====================================================================
class ClarityChecker:
    def __init__(self) -> None:
        self.module: ClarityCheckerModule = ClarityCheckerModule()

    async def __call__(self, message_history: list[BaseMessage], clarity_history: list[BaseMessage], human_message: HumanMessage) -> bool:
        """Standard, non-streaming async call path that parses text to a boolean."""
        raw_result = await self.module.aforward(message_history, clarity_history, human_message)
        return "true" in raw_result.strip().lower()

    async def stream(
        self, 
        message_history: list[BaseMessage], 
        clarity_history: list[BaseMessage], 
        human_message: HumanMessage
    ) -> AsyncGenerator[str | bool, None]:
        """Streams the text tokens first, and yields a native boolean at the very end."""
        
        # FIX 3: Removed the bad nested loop logic and returned the generator coroutine
        raw_stream = await self.module.stream(message_history, clarity_history, human_message)
        
        final_prediction = None

        async for chunk in raw_stream:
            if isinstance(chunk, dspy.Prediction):
                final_prediction = chunk
            else:
                # Yield text tokens to the UI while generating
                yield chunk

        # Parse and yield the final boolean evaluation right before closing
        if final_prediction is not None:
            is_cleared_bool = "true" in final_prediction.is_cleared.strip().lower()
            yield is_cleared_bool
