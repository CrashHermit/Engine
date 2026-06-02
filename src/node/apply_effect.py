from dataclasses import replace

from src.core.mechanic.effect import (
    effect_from_tier,
    effect_segments,
    is_defeated,
    potency_shift,
)
from src.core.mechanic.harm import apply_wounds
from src.core.model.entity import EntityKind
from src.core.model.location import EntityData
from src.core.model.threat import Channel
from src.state import GraphState


class ApplyEffectNode:
    """The effect-on-target half of the roll. Finds the action's target among
    the scene entities, scales the player's effect from the same action tier
    (shifted by potency), and fills the target's clock. Pure state mutation —
    persistence (and removing a defeated entity) happens post-turn in the
    coordinator, per the side-effect boundary."""

    async def __call__(self, state: GraphState) -> dict:
        target = self._find_target(state)
        # Only living foes take clock damage; props can't be "defeated".
        if target is None or target.kind != EntityKind.CREATURE or state.roll_result is None:
            return {}

        pool = self._pool_for_attribute(state)
        effect = potency_shift(effect_from_tier(state.roll_result.tier), pool, target.danger)
        segments = effect_segments(effect)
        if segments <= 0:
            return {}

        result = apply_wounds(target.wound, segments)
        updated = replace(target, wound=result.pool)
        scene = [updated if e.id == target.id else e for e in state.scene_entities]
        out: dict = {"scene_entities": scene}
        if is_defeated(result.pool):
            out["defeated_target"] = target.name
        return out

    def _find_target(self, state: GraphState) -> EntityData | None:
        name = (state.target_entity or "").strip().lower()
        if not name:
            return None
        for e in state.scene_entities:
            if e.name.lower() == name:
                return e
        # Fall back to a loose match so minor LLM rephrasings still land.
        for e in state.scene_entities:
            if name in e.name.lower() or e.name.lower() in name:
                return e
        return None

    @staticmethod
    def _pool_for_attribute(state: GraphState) -> int:
        match state.attribute:
            case Channel.CORPUS:
                return state.corpus_rating
            case Channel.MENS:
                return state.mens_rating
            case Channel.ANIMA:
                return state.anima_rating
            case _:
                return 0
