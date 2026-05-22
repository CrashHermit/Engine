from module.base import BaseModule
from dspy import (
    InputField, 
    OutputField, 
    Signature, 
)

class QuestionGeneratorSignature(Signature):
    """
    Generate a single clarifying DM-style question for ambiguous player input.
    """

    message_history: str = InputField(default="", description="The chat history")
    clarity_history: str = InputField(default="", description="Accumulated player responses")
    human_message: str = InputField(default="", description="The message to clarify")
    question: str = OutputField(description="A single focused clarifying question.")

class QuestionGeneratorModule(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            signature=QuestionGeneratorSignature,
            stream_fields=["question"],
        )
