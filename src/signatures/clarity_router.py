from dspy import Signature, InputField, OutputField


class ClarityRouterSignature(Signature):
    """
    You are a clarity router. Your job is to route the player's message to the appropriate generator.
    If the intent is clear, return true. If the intent isn't clear, return false.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's current message or action")
    clarity_history: str = InputField(default="", description="The clarity history so far")
    
    is_clarity_achieved: bool = OutputField(description="Whether the intent is clear")
