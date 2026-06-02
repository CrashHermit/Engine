from dataclasses import replace

from dspy import Predict, Prediction

from src.core.model.entity import EntityStatus
from src.lm import lm
from src.signature.reengage import ReengagementSignature
from src.state import GraphState


class ReengageNode:
    """Turn-start durability check. Suspended creatures (a pillar broken, not
    destroyed) can come back: for each one, an LLM judges whether the player's
    latest action satisfies its returns_when. Reactivated creatures reset the
    broken pillar's clock (they rallied / re-noticed), rejoin the threat
    fan-out, and are narrated returning. Short-circuits with no LLM call when
    nothing is suspended."""

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=ReengagementSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        suspended = [e for e in state.scene_entities if e.status == EntityStatus.SUSPENDED]
        if not suspended:
            return {}

        player_action = state.human_message.content if state.human_message else ""
        scene = list(state.scene_entities)
        returned: list[str] = []

        for entity in suspended:
            prediction: Prediction = await self._program.aforward(
                creature=entity.name,
                broken_condition=entity.broken_pillar.value if entity.broken_pillar else "",
                returns_when=entity.returns_when,
                player_action=player_action,
                recent_events=state.prior_prose or "",
            )
            if not prediction.returns:
                continue
            clocks = dict(entity.clocks)
            if entity.broken_pillar is not None:
                clocks[entity.broken_pillar] = 0  # it rallied / re-noticed — that pillar resets
            reactivated = replace(
                entity,
                status=EntityStatus.ACTIVE,
                broken_pillar=None,
                returns_when="",
                clocks=clocks,
            )
            scene = [reactivated if e.id == entity.id else e for e in scene]
            returned.append(entity.name)

        if not returned:
            return {}
        note = "; ".join(f"{n} re-engages and is a threat again" for n in returned)
        return {"scene_entities": scene, "returned_targets": returned, "reengagement_note": note}
