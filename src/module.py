from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string
from typing import AsyncGenerator
import dspy

lm: dspy.LM = dspy.LM(
        model='openrouter/google/gemma-4-26b-a4b-it', 
        api_key="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",
        temperature=0.7
    )
dspy.configure(lm=lm)


class NarratorSignature(dspy.Signature):
    """
    You are a narrator, you will take the input from the human and the chat history and you will return the narration of the message.
    """
    message_history: list[BaseMessage] = dspy.InputField(default_factory=list, description="The chat history")
    human_message: HumanMessage = dspy.InputField(default=HumanMessage(content="", name=""), description="The message to predict")
    ai_message: str = dspy.OutputField(default="", description="The narration of the message")

class NarratorModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.narrator_prediction: dspy.ChainOfThought = dspy.ChainOfThought(signature=NarratorSignature)
        
    def aforward(self, message_history: list[BaseMessage], human_message: HumanMessage) -> AIMessage:
        prediction: dspy.Prediction = self.narrator_prediction(
            message_history=message_history,
            human_message=human_message
        )
        
        return AIMessage(content=prediction.ai_message, name="Narrator")




class NarratorSignature2(dspy.Signature):
    """
    You are a narrator, you will take the input from the human and the chat history and you will return the narration of the message.
    """
    message_history: str = dspy.InputField(default="", description="The chat history")
    human_message: str = dspy.InputField(default=HumanMessage(content="", name=""), description="The message to predict")
    ai_message: str = dspy.OutputField(default="", description="The narration of the message")

class NarratorModule2(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.narrator_prediction: dspy.ChainOfThought = dspy.ChainOfThought(signature=NarratorSignature2)
        self._streaming_engine = dspy.streamify(
            program=self,
            stream_listeners=[dspy.streaming.StreamListener(signature_field_name="ai_message")],
            is_async_program=True,
        )

    async def aforward(
        self, message_history: list[BaseMessage], human_message: HumanMessage
    ) -> dspy.Prediction:
        message_history_str: str = get_buffer_string(messages=message_history)
        human_message_str: str = get_buffer_string(messages=[human_message])
        return await self.narrator_prediction.acall(
            message_history=message_history_str,
            human_message=human_message_str,
        )

    async def stream(
        self,
        message_history: list[BaseMessage],
        human_message: HumanMessage,
    ) -> AsyncGenerator[dspy.streaming.StreamResponse | dspy.Prediction, None]:
        stream = self._streaming_engine(
            message_history=message_history,
            human_message=human_message,
        )
        async for chunk in stream:
            yield chunk