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
    chat_history: list[str] = dspy.InputField(default_factory=list, description="The chat history")
    message: str = dspy.InputField(default="", description="The message to predict")
    response: str = dspy.OutputField(default="", description="The narration of the message")

class NarratorModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.narrator_prediction = dspy.ChainOfThought(signature=NarratorSignature)
        
    def aforward(self, chat_history: list[BaseMessage], message: HumanMessage) -> AIMessage:
        
        string_history = []
        for msg in chat_history:
            prefix = "User" if isinstance(msg, HumanMessage) else "Assistant"
            string_history.append(f"{prefix}: {msg.content}")
            
        string_message = message.content

        prediction: dspy.Prediction = self.narrator_prediction(
            chat_history=string_history, 
            message=string_message
        )
        
        return AIMessage(content=prediction.response)

