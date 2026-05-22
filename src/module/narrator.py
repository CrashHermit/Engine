import dspy


class NarratorSignature(dspy.Signature):
    """
    You are a narrator, you will take the input from the human and the chat history and you will return the narration of the message.
    """

    message_history: str = dspy.InputField(default="", description="The chat history")
    human_message: str = dspy.InputField(default="", description="The message to narrate")
    ai_message: str = dspy.OutputField(description="The narration of the message")


class NarratorModule(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.predict: dspy.ChainOfThought = dspy.ChainOfThought(signature=NarratorSignature)

    async def aforward(self, message_history: str, human_message: str) -> dspy.Prediction:
        return await self.predict.acall(
            message_history=message_history,
            human_message=human_message,
        )
