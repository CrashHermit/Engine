from dspy import (
    InputField,
    OutputField,
    Signature,
)

class NarratorSignature(Signature):
    """
    You are a narrator for a text adventure game. Given the player's current location
    and the conversation history, respond in-character to the player's action or message.
    Use the ordered action list to structure your narration — depict each action in
    sequence. Keep the tone immersive and descriptive.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's intended action")
    action_list: str = InputField(default="", description="Ordered list of discrete actions to narrate through")
    ai_message: str = OutputField(description="The narrator's in-character response")
