from src.core.model.resist import FinalScaffold, HeldScaffold, ResistAction


def mundane_directive(lead_up: str) -> str:
    return (
        f"Narrate this action: {lead_up}. "
        "No threat, no consequence, no resist offer. "
        "Describe what happens."
    )


def held_directive(scaffold: HeldScaffold) -> str:
    ambiguities = ", ".join(scaffold.ambiguity_wedge)
    return (
        f"Write the impact moment for this contested beat. "
        f"The impact landed on: {scaffold.impact_focus}. "
        "You MUST commit to the impact (it happened, the character feels it) "
        "but you MUST NOT commit to its depth, finality, or lasting shape — "
        f"these dimensions are deliberately held: {ambiguities}. "
        f"End the prose on this beat: {scaffold.tension_close}. "
        "After the prose, on a new line, present the resist offer to the "
        f"player: {scaffold.resist_options_text}"
    )


def final_directive(scaffold: FinalScaffold, resist_action: ResistAction) -> str:
    resolutions = ", ".join(scaffold.resolutions)
    base = (
        "Write the resolution prose for this beat. Continue from the prior "
        "prose in context, matching its voice and rhythm. Collapse each of "
        f"these held dimensions: {resolutions}. "
    )
    if resist_action != ResistAction.ENDURE:
        base += (
            "Weave the player's framing naturally into the prose: "
            f'"{scaffold.incorporate_player_text}". '
        )
    base += f"End on this beat: {scaffold.closing_beat}."
    return base

def resolution_directive(consequence: FinalScaffold, action: ResistAction, flavor: str) -> str:
    if action == ResistAction.ENDURE:
        return (
            "In one or two sentences, continuing from the prior prose and matching "
            f"its voice, narrate how this consequence lands as the character endures it: "
            f"{consequence}. Do NOT present any resist offer."
        )
    return (
        "In one or two sentences, continuing from the prior prose and matching its "
        f"voice, narrate how the character's resistance plays out against this "
        f'consequence: {consequence}. The player framed it as: "{flavor}". Show the '
        "consequence reduced but still real. Do NOT present any resist offer."
    )