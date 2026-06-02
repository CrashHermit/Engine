from src.state import GraphState


class AmbushNode:
    """Entry to the world-acts path: a hostile creature strikes on a turn the
    player spent on something non-contested. Marks the turn as an ambush and
    seeds the contested beat from the player's action so the threat classifier
    and planners have context (the player studies the map → the spider drops)."""

    async def __call__(self, state: GraphState) -> dict:
        beat = state.human_message.content if state.human_message else ""
        return {"is_ambush": True, "contested_beat": beat}
