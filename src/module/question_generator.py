import dspy

from module.base import BaseModule


class QuestionGeneratorSignature(dspy.Signature):
    """Generate a single clarifying DM-style question for ambiguous player input."""

    message_history: str = dspy.InputField(default="", description="The chat history")
    clarity_history: str = dspy.InputField(default="", description="Accumulated player responses")
    human_message: str = dspy.InputField(default="", description="The message to clarify")
    question: str = dspy.OutputField(description="A single focused clarifying question.")


class QuestionGeneratorModule(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            signature=QuestionGeneratorSignature,
            stream_fields=["question"],
        )
