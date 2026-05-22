import dspy


class ClarityCheckerSignature(dspy.Signature):
    """Determine if player intent is clear enough to proceed."""

    message_history: str = dspy.InputField(default="", description="The chat history")
    clarity_history: str = dspy.InputField(default="", description="Accumulated player responses")
    human_message: str = dspy.InputField(default="", description="The message to evaluate")
    is_cleared: str = dspy.OutputField(description="Whether the message is clear. Return exactly True or False with reasoning.")


class ClarityCheckerModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.predict: dspy.ChainOfThought = dspy.ChainOfThought(signature=ClarityCheckerSignature)

    async def aforward(
        self,
        message_history: str,
        clarity_history: str,
        human_message: str,
    ) -> dspy.Prediction:
        return await self.predict.acall(
            message_history=message_history,
            clarity_history=clarity_history,
            human_message=human_message,
        )
