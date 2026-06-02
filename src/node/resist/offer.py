from langgraph.types import interrupt

from src.core.mechanic.threat_envelope import describe_threat
from src.state import GraphState


class ResistOfferNode:
    """Per-threat interrupt. Replay-pure: it only reads state and interrupts.
    The payload carries the prior prose (cohesive setup before the first offer,
    or the previous threat's resolution line thereafter) plus this threat's
    consequence and the live stress total — the informed gamble."""

    async def __call__(self, state: GraphState) -> dict:
        threat = state.current_threat
        consequence = describe_threat(threat)
        response: str = interrupt(
            {
                "offer": f"{consequence} — resist or endure?",
                "consequence": consequence,
                "threat_id": threat.id if threat else "",
                "stress_now": state.stress,
                "narration": state.prior_prose or "",
            }
        )
        return {"resist_response": response}