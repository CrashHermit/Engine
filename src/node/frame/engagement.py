from __future__ import annotations

from dataclasses import replace

from dspy import InputField, OutputField, Predict, Prediction, Signature

from src.core.model.entity import EntityKind, EntityStance, EntityStatus
from src.core.model.location import EntityData
from src.lm import lm
from src.state import GraphState


class EngagementSignature(Signature):
    """Decide a creature's engagement posture toward the player for this turn.

    Both first contact (aggro) and a neutralized foe re-engaging use this one
    judgment. Given the creature's nature, its current situation, and what the
    player just did, choose its new posture:

    - hostile: it acts against the player NOW (strikes, attacks, re-engages).
    - wary: it has noticed and is tense/poised, but has NOT committed to attack.
    - unaware: no change — it remains oblivious or stays withdrawn.

    Judge from the creature's nature and the fiction. A predatory or territorial
    creature turns hostile when the player gets close, encroaches, attacks it,
    or makes itself obvious; it may pass through wary first if contact is faint.
    A neutral, friendly, or skittish creature does NOT turn hostile on its own
    (a skittish one would rather flee). A creature the player directly attacks or
    provokes is hostile. Be conservative for ambient, decisive on real provocation.
    """

    creature: str = InputField(description="The creature")
    nature: str = InputField(
        description=(
            "Its disposition (predatory/territorial/guardian/skittish/neutral/friendly)"
        )
    )
    situation: str = InputField(
        description="Its current posture/status and any re-engage condition"
    )
    player_action: str = InputField(description="What the player just did this turn")
    recent_events: str = InputField(
        default="", description="Recent narration, for context"
    )

    posture: EntityStance = OutputField(
        description="New posture: hostile / wary / unaware"
    )


class EngagementNode:
    """Run the turn-start engagement check — the synthesis aggro model.

    For every creature that is not already an active threat (unaware/wary
    newcomers AND suspended foes), an LLM judges its new posture from its
    disposition + the fiction. A creature turning HOSTILE joins the threat
    fan-out; a suspended foe turning HOSTILE re-engages (its broken pillar's
    clock resets). The fan-out is the 'GM' that arbitrates who actually
    threatens. Short-circuits with no LLM call when there are no such
    creatures.
    """

    def __init__(self) -> None:
        self._program: Predict = Predict(signature=EngagementSignature)
        self._program.lm = lm

    async def __call__(self, state: GraphState) -> dict:
        candidates = [
            e
            for e in state.get("scene_entities", [])
            if e.kind == EntityKind.CREATURE
            and e.status != EntityStatus.GONE
            and not (
                e.status == EntityStatus.ACTIVE and e.stance == EntityStance.HOSTILE
            )
        ]
        if not candidates:
            return {}

        player_action = (
            state.get("human_message").content if state.get("human_message") else ""
        )
        scene = list(state.get("scene_entities", []))
        returned: list[str] = []
        notes: list[str] = []
        changed = False

        for entity in candidates:
            prediction: Prediction = await self._program.aforward(
                creature=entity.name,
                nature=entity.disposition.value,
                situation=self._situation(entity),
                player_action=player_action,
                recent_events=state.get("prior_prose") or "",
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
            broken = (
                entity.broken_pillar.value if entity.broken_pillar else "a condition"
            )
            condition = entity.returns_when or "the situation turns against the player"
            return (
                f"It was neutralized ({broken} broken) and withdrew from the fight; "
                f"it re-engages when: {condition}."
            )
        if entity.stance == EntityStance.WARY:
            return (
                "It has noticed the player and is tense and poised, "
                "but has not committed to attacking."
            )
        return "It is unaware of the player / lurking — it has not noticed them yet."

    def _apply(
        self,
        entity: EntityData,
        posture: EntityStance,
        returned: list[str],
        notes: list[str],
    ) -> EntityData | None:
        """Map the judged posture onto the entity.

        Return the updated entity, or None if nothing changes.
        """
        if entity.status == EntityStatus.SUSPENDED:
            if posture != EntityStance.HOSTILE:
                return None  # stays withdrawn
            clocks = dict(entity.clocks)
            if entity.broken_pillar is not None:
                clocks[entity.broken_pillar] = (
                    0  # rallied / re-noticed — that pillar resets
                )
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
