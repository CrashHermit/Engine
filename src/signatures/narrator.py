from dspy import (
    InputField, 
    OutputField, 
    Signature, 
    LM, 
    configure,
)
import os
from dotenv import load_dotenv
load_dotenv()

lm: LM = LM(
    model=os.getenv("LM_MODEL", "openrouter/google/gemma-4-26b-a4b-it"),
    api_key=os.getenv("LM_API_KEY"),
    temperature=0.7,
)
configure(lm=lm)

class NarratorSignature(Signature):
    """
    You are a narrator, you will take the input from the human and the chat history
    and you will return the narration of the message.
    """

    message_history: str = InputField(default="", description="The chat history")
    human_message: str = InputField(description="The message to narrate")
    ai_message: str = OutputField(description="The narration of the message")
