from dspy import InputField, OutputField, Signature


class IntentSynthesizerSignature(Signature):
    """
    You are an intent synthesizer. Given the player's original message and the
    clarification Q&A that followed, produce a single clear, complete statement
    of what the player intends to do. The synthesized message should read as if
    the player wrote it themselves — first person, concrete, and actionable.
    Incorporate all resolved details from the clarification exchanges.
    """

    character_description: str = InputField(
        default="", description="A description of the player character"
    )
    location_description: str = InputField(
        default="", description="A description of the current location"
    )
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's original message or action")
    intent_alignment_history: str = InputField(
        description="The clarification Q&A that resolved the player's intent"
    )

    synthesized_message: str = OutputField(
        description="A single clear statement of the player's full intent"
    )
