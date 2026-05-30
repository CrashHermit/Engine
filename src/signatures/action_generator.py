from dspy import InputField, OutputField, Signature


class ActionGeneratorSignature(Signature):
    """
    You are an action decomposer for a text adventure game. Given the player's
    stated intent, break it down into an ordered list of discrete, concrete
    actions that the narrator should depict. Each action should be a single
    clear step. Order them in the sequence they would naturally occur.
    Only include actions the character can realistically perform given their
    description and current location.
    """

    character_description: str = InputField(
        default="", description="A description of the player character"
    )
    location_description: str = InputField(
        default="", description="A description of the current location"
    )
    entities_at_location: str = InputField(
        default="",
        description="Entities present in the current location, each formatted as 'Name: description. Location: scene_position'",
    )
    message_history: str = InputField(default="", description="The conversation history so far")
    human_message: str = InputField(description="The player's intended action")

    action_list: list[str] = OutputField(description="Ordered list of discrete actions to perform")
