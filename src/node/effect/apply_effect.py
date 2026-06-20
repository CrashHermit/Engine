from dataclasses import replace

from src.core.mechanic.economy import add_stress
from src.core.mechanic.effect import (
    effect_from_tier,
    effect_segments,
    outcome_clause,
    pillar_capacity,
    potency_shift,
    returns_when_for,
)
from src.core.mechanic.push import PUSH_FOR_EFFECT_SEGMENTS, PUSH_FOR_EFFECT_STRESS
from src.core.model.entity import EntityData, EntityKind, EntityStatus, ThreatPillar
from src.state import GraphState, action_intent, pool_for


class ApplyEffectNode:
    """Apply the effect-on-target half of the roll.

    Finds the action's target and the pillar the action attacks, scales effect
    from the same action tier (shifted by potency), and fills that pillar's
    clock. Breaking a pillar neutralises the creature — EXISTS removes it
    (GONE), any other pillar suspends it. Pure state mutation; persistence /
    removal happens post-turn in the coordinator.
    """

    async def __call__(self, state: GraphState) -> dict:
        intent = action_intent(state)
        target = self._find_target(intent.target, state.get("scene_entities", []))
        # Only living foes can be de-threated; props can't be "defeated".
        if (
            target is None
            or target.kind != EntityKind.CREATURE
            or state.get("roll_result") is None
        ):
            return {}

        pillar = intent.pillar
        capacity = pillar_capacity(target.danger, pillar, target.pillar_profile)
        if capacity <= 0:  # immune to this pillar (profile omits it)
            return {
                "resolution_outcome": (
                    f"The {target.name} cannot be affected this way "
                    "(immune to this approach) — "
                    "the attempt has no effect; make that clear to the player."
                )
            }

        pool = pool_for(state, intent.attribute)
        segments = effect_segments(
            potency_shift(
                effect_from_tier(state.get("roll_result").tier), pool, target.danger
            )
        )
        if segments <= 0:
            return {}

        out: dict = {}
        # Push for effect (action-level): spend stress for one extra segment.
        # Only when the action already landed effect — a miss can't be pushed,
        # and the player isn't charged for nothing.
        pushed = False
        if intent.push:
            segments += PUSH_FOR_EFFECT_SEGMENTS
            stress_result = add_stress(
                state.get("stress", 0), state.get("trauma", 0), PUSH_FOR_EFFECT_STRESS
            )
            out.update(
                stress=stress_result.stress,
                trauma=stress_result.trauma,
                trauma_gained=state.get("trauma_gained", False)
                or stress_result.trauma_gained,
                character_lost=state.get("character_lost", False) or stress_result.lost,
            )
            pushed = True

        filled = min(capacity, target.clocks.get(pillar, 0) + segments)
        clocks = {**target.clocks, pillar: filled}

        status = target.status
        broken_pillar = target.broken_pillar
        returns_when = target.returns_when
        outcome = ""
        if filled >= capacity:
            broken_pillar = pillar
            outcome = outcome_clause(pillar, target.name)
            if pillar == ThreatPillar.EXISTS:
                status = EntityStatus.GONE
                out["defeated_target"] = target.name
            else:
                status = EntityStatus.SUSPENDED
                returns_when = returns_when_for(pillar)
                out["suspended_target"] = target.name

        if pushed:
            outcome = (
                f"{outcome} The character pushed themselves hard for this — show the "
                "extra exertion and its toll."
            ).strip()
        if outcome:
            out["resolution_outcome"] = outcome

        updated = replace(
            target,
            clocks=clocks,
            status=status,
            broken_pillar=broken_pillar,
            returns_when=returns_when,
        )
        out["scene_entities"] = [
            updated if e.id == target.id else e for e in state.get("scene_entities", [])
        ]
        return out

    def _find_target(
        self, target: str, entities: list[EntityData]
    ) -> EntityData | None:
        name = target.strip().lower()
        if not name:
            return None
        for e in entities:
            if e.name.lower() == name:
                return e
        # Fall back to a loose match so minor LLM rephrasings still land.
        for e in entities:
            if name in e.name.lower() or e.name.lower() in name:
                return e
        return None
