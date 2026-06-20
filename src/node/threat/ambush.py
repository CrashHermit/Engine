from src.state import GraphState


class AmbushNode:
    """Enter the world-acts path when a hostile creature strikes.

    This occurs on a turn the player spent on something non-contested. Marks
    the turn as an ambush and seeds the contested beat from the player's
    action so the threat classifier and planners have context (the player
    studies the map → the spider drops).
    """

    async def __call__(self, state: GraphState) -> dict:
        beat = state.get("human_message").content if state.get("human_message") else ""
        return {"is_ambush": True, "contested_beat": beat}
