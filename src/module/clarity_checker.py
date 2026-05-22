import dspy

from module.base import BaseModule


class ClarityCheckerSignature(dspy.Signature):
    """Determine if player intent is clear enough to proceed."""

    message_history: str = dspy.InputField(default="", description="The chat history")
    clarity_history: str = dspy.InputField(default="", description="Accumulated player responses")
    human_message: str = dspy.InputField(default="", description="The message to evaluate")
    is_cleared: str = dspy.OutputField(description="Whether the message is clear. Return exactly True or False with reasoning.")


class ClarityCheckerModule(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            signature=ClarityCheckerSignature,
            stream_fields=["is_cleared"],
        )
