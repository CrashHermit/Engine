from dspy import InputField, OutputField, Signature


class ReengagementSignature(Signature):
    """
    A creature was neutralized without being destroyed — a threat pillar was
    broken, so it is currently out of the scene (fled, cowed, hidden-from,
    disabled, or kept at bay). Given what the player just did and the condition
    under which it would re-engage, decide whether it returns to the fray NOW.

    Be conservative: only return true if the player's action (or the unfolding
    situation) plausibly satisfies the return condition. A creature that fled in
    terror does not come back because the player tied their boot; it comes back
    if cornered, if the player looks weak, or if it gathers its nerve.
    """

    creature: str = InputField(description="The neutralized creature")
    broken_condition: str = InputField(description="Which condition was broken (e.g. willing, in_reach)")
    returns_when: str = InputField(description="The fiction under which it re-engages")
    player_action: str = InputField(description="What the player just did this turn")
    recent_events: str = InputField(default="", description="Recent narration, for context")

    returns: bool = OutputField(description="Whether the creature re-engages this turn")
