from dataclasses import replace

from dspy import Predict, Prediction

from src.core.model.entity import EntityKind, EntityStance, EntityStatus
from src.core.model.location import EntityData
from src.lm import lm
from src.signature.engagement import EngagementSignature
from src.state import GraphState


class EngagementNode:
    """Turn-start engagement check — the synthesis aggro model. For every
    creature that is not already an active threat (unaware/wary newcomers AND
    suspended foes), an LLM judges its new posture from its disposition + the
    fiction. A creature turning HOSTILE joins the threat fan-out; a suspended
    foe turning HOSTILE re-engages (its broken pillar's clock resets). The
    fan-out is the 'GM' that arbitrates who actually threatens. Short-circuits
    with no LLM call when there are no such creatures."""

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=EngagementSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        candidates = [
            e
            for e in state.scene_entities
            if e.kind == EntityKind.CREATURE
            and e.status != EntityStatus.GONE
            and not (e.status == EntityStatus.ACTIVE and e.stance == EntityStance.HOSTILE)
        ]
        if not candidates:
            return {}

        player_action = state.human_message.content if state.human_message else ""
        scene = list(state.scene_entities)
        returned: list[str] = []
        notes: list[str] = []
        changed = False

        for entity in candidates:
            prediction: Prediction = await self._program.aforward(
                creature=entity.name,
                nature=entity.disposition.value,
                situation=self._situation(entity),
                player_action=player_action,
                recent_events=state.prior_prose or "",
            )
            posture = prediction.posture
            updated = self._apply(entity, posture, returned, notes)
            if updated is not None:
                scene = [updated if e.id == entity.id else e for e in scene]
                changed = True

        if not changed:
            return {}
        out: dict = {"scene_entities": scene}
        if returned:
            out["returned_targets"] = returned
        if notes:
            out["engagement_note"] = "; ".join(notes)
        return out

    @staticmethod
    def _situation(entity: EntityData) -> str:
        if entity.status == EntityStatus.SUSPENDED:
            broken = entity.broken_pillar.value if entity.broken_pillar else "a condition"
            return (
                f"It was neutralized ({broken} broken) and withdrew from the fight; "
                f"it re-engages when: {entity.returns_when or 'the situation turns against the player'}."
            )
        if entity.stance == EntityStance.WARY:
            return "It has noticed the player and is tense and poised, but has not committed to attacking."
        return "It is unaware of the player / lurking — it has not noticed them yet."

    def _apply(
        self, entity: EntityData, posture: EntityStance, returned: list[str], notes: list[str]
    ) -> EntityData | None:
        """Map the judged posture onto the entity; return the updated entity, or
        None if nothing changes."""
        if entity.status == EntityStatus.SUSPENDED:
            if posture != EntityStance.HOSTILE:
                return None  # stays withdrawn
            clocks = dict(entity.clocks)
            if entity.broken_pillar is not None:
                clocks[entity.broken_pillar] = 0  # rallied / re-noticed — that pillar resets
            returned.append(entity.name)
            notes.append(f"{entity.name} re-engages and is a threat again")
            return replace(
                entity,
                status=EntityStatus.ACTIVE,
                stance=EntityStance.HOSTILE,
                broken_pillar=None,
                returns_when="",
                clocks=clocks,
            )
        # ACTIVE, currently UNAWARE or WARY
        if posture == EntityStance.HOSTILE:
            notes.append(f"{entity.name} turns hostile and moves to attack")
            return replace(entity, stance=EntityStance.HOSTILE)
        if posture == EntityStance.WARY and entity.stance != EntityStance.WARY:
            notes.append(f"{entity.name} notices the player and grows wary")
            return replace(entity, stance=EntityStance.WARY)
        return None
