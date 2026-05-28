from dspy import (
    InputField, 
    OutputField, 
    Signature, 
)

class NarratorSignature(Signature):
    """
    You are a narrator for a text adventure game. Given the player's current location
    and the conversation history, respond in-character to the player's action or message.
    Keep the tone immersive and descriptive.
    """

    character_name: str = InputField(default="", description="The player character's name")
    character_description: str = InputField(default="", description="A description of the player character")
    location_name: str = InputField(default="", description="The name of the current location")
    location_description: str = InputField(default="", description="A description of the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's current message or action")
    ai_message: str = OutputField(description="The narrator's in-character response")
