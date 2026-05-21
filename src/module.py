from typing import Any, Literal


from dspy.predict.chain_of_thought import ChainOfThought


from dspy.primitives.prediction import Prediction


import dspy
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

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
        self.narrator_prediction: ChainOfThought = dspy.ChainOfThought(signature=NarratorSignature)
        
    def aforward(self, message_history: list[BaseMessage], human_message: HumanMessage) -> AIMessage:
        prediction: dspy.Prediction = self.narrator_prediction(
            message_history=message_history,
            human_message=human_message
        )
        
        return AIMessage(content=prediction.ai_message, name="Narrator")