from dspy import Signature, InputField, OutputField

class ClarityGeneratorSignature(Signature):
    """
    You are a question generator. Your job is to take the current message history and the player's current message
    and clarify whatt the intent of the player is. Take into account the character's location, personality, entities in the scene
    and the overall context of the game. If the player shouldn't reasonably be able to perform an action, ask them to try something else.
    Output one question at a time, with an explination of why you are asking the question. If the intent isn't clearn yet, ask them a follow up
    question until an understanding of the intent is reached.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's current message or action")
    clarity_history: str = InputField(default="", description="The clarity history so far")
    
    question: str = OutputField(description="The question to ask the player")
