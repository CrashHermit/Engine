from langgraph.types import interrupt

from src.state import GraphState


class ResistOfferNode:
    """Pauses the graph after the held narration and waits for the player's
    resistance response. On resume, stores the player's text as resist_response
    so the resist_push_parser can classify it."""

    async def __call__(self, state: GraphState) -> dict:
        response: str = interrupt({"offer": "Resist, push for effect, or endure?"})
        return {"resist_response": response}
