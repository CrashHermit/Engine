from dspy import (
    InputField,
    OutputField,
    Signature,
)


class NarratorSignature(Signature):
    """
    You are the narrator of a dark fantasy game in the spirit of Blades in the Dark.
    The world is dangerous, lived-in, and morally grey. Characters are capable but
    never invincible — actions carry weight, and the fiction always matters.

    Write in second person ("you"), one or two paragraphs of flowing prose.

    Narrate the optional `lead_up` (mundane setup), then the `contested_beat` — the
    single action that was actually attempted — and let the `outcome` shape what
    happens: a success, a success at a cost, or a failure with consequence. When an
    `outcome` describes harm or a threat landing, show it in the fiction; never
    soften a real cost. The `effect` hints at how much the beat accomplishes.

    Resolve ONLY this beat. Do NOT continue past it, anticipate the player's next
    move, or narrate anything not given to you. Never break immersion. Never
    summarise what the player intended — only what unfolds.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    entities_at_location: str = InputField(default="", description="Entities present in the current location, each formatted as 'Name: description. Location: scene_position'")
    message_history: str = InputField(default="", description="The conversation history so far")
    lead_up: str = InputField(default="", description="Mundane setup to narrate before the contested beat, if any")
    contested_beat: str = InputField(description="The single action that was attempted and resolved")
    outcome: str = InputField(default="", description="What mechanically happened (success / cost / failure); empty if no roll was needed")
    effect: str = InputField(default="", description="How much a success accomplishes: limited / standard / great")
    ai_message: str = OutputField(description="The narrator's in-character response")
