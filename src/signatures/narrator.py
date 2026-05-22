from dspy import InputField, OutputField, Signature


class NarratorSignature(Signature):
    """
    You are a narrator, you will take the input from the human and the chat history
    and you will return the narration of the message.
    """

    message_history: str = InputField(default="", description="The chat history")
    human_message: str = InputField(description="The message to narrate")
    ai_message: str = OutputField(description="The narration of the message")
