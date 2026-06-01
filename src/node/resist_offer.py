from langgraph.types import interrupt

from src.state import GraphState


class ResistOfferNode:
    """Pauses the graph after the held narration and waits for the player's
    resistance response. On resume, stores the player's text as resist_response
    so the resist_push_parser can classify it.

    The held narration is carried in the interrupt payload. This node runs
    inside the resolution subgraph, and a subgraph's internal channel writes
    (here, the narrator's ai_message) do NOT propagate to the parent graph
    while the subgraph is paused on an interrupt — only the interrupt payload
    crosses that boundary. Putting the prose in the payload is what lets the
    coordinator show the consequence before presenting the resist offer."""

    async def __call__(self, state: GraphState) -> dict:
        response: str = interrupt(
            {
                "offer": "Resist, push for effect, or endure?",
                "narration": state.prior_prose or "",
            }
        )
        return {"resist_response": response}
