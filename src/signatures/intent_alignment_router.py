from dspy import Signature, InputField, OutputField


class IntentAlignmentRouterSignature(Signature):
    """
    You are an intent alignment router. Determine whether the player's message
    expresses clear, actionable intent given the current context and any prior
    clarification exchanges. Return true only when you have enough information
    to act. Return false if the intent is ambiguous, physically impossible for
    this character, or contradicts the current context.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's current message or action")
    intent_alignment_history: str = InputField(default="", description="The prior clarification Q&A for this action")

    is_clarity_achieved: bool = OutputField(description="Whether the player's intent is clear enough to act on")
