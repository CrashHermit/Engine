from __future__ import annotations

from langgraph.types import interrupt

from src.core.model.message import Message
from src.state import GraphState


class IntentClarificationNode:
    """Pause the graph and wait for the player's answer to the clarifying question.

    The question is produced by the question generator. The graph stays
    suspended (state frozen in the checkpointer) until it is resumed with
    ``Command(resume=<player answer>)``. On resume this node re-runs from the
    top, ``interrupt()`` returns the player's answer, and we append it to the
    intent alignment history before routing back to the router for
    re-evaluation.
    """

    async def __call__(self, state: GraphState) -> dict:
        answer: str = interrupt({"question": state.get("question")})
        answer_message = Message(
            role="human",
            content=answer,
            name=state.get("human_message").name if state.get("human_message") else "",
        )
        return {"intent_alignment_history": [answer_message]}
