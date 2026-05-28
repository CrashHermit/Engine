from dspy import Signature, InputField, OutputField


class IntentQuestionGeneratorSignature(Signature):
    """
    You are an intent question generator for a text adventure game. The player's
    message is ambiguous or unclear. Ask one focused question to resolve the most
    important unknown. Take into account the character's abilities, location,
    and prior clarification exchanges. If the player is attempting something their
    character cannot reasonably do, explain why and ask them to reconsider.
    Ask only one question at a time with a brief explanation of why you need it.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's current message or action")
    intent_alignment_history: str = InputField(default="", description="The prior clarification Q&A for this action")

    question: str = OutputField(description="One clarification question to ask the player")
