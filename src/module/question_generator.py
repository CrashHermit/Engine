import dspy


class QuestionGeneratorSignature(dspy.Signature):
    """Generate a single clarifying DM-style question for ambiguous player input."""

    message_history: str = dspy.InputField(default="", description="The chat history")
    clarity_history: str = dspy.InputField(default="", description="Accumulated player responses")
    human_message: str = dspy.InputField(default="", description="The message to clarify")
    question: str = dspy.OutputField(description="A single focused clarifying question.")


class QuestionGeneratorModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.predict: dspy.ChainOfThought = dspy.ChainOfThought(signature=QuestionGeneratorSignature)

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
