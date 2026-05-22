import dspy

from module.base import BaseModule


class NarratorSignature(dspy.Signature):
    """
    You are a narrator, you will take the input from the human and the chat history and you will return the narration of the message.
    """

    message_history: str = dspy.InputField(default="", description="The chat history")
    human_message: str = dspy.InputField(default="", description="The message to narrate")
    ai_message: str = dspy.OutputField(description="The narration of the message")


class NarratorModule(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            signature=NarratorSignature,
            stream_fields=["reasoning", "ai_message"],
            predictor=dspy.ChainOfThought,
        )
