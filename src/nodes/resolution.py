import random

from src.core.mechanics import Magnitude, Position, roll_pool, scale_threat
from src.state import GraphState

# --- Phase 1 framing stubs --------------------------------------------------
# Hardcoded stand-ins for the DSPy framing classifiers that arrive in Phase 2
# (attribute / effect / threat-type / threat-magnitude / threat-channel, #18).
_STUB_ATTRIBUTE = "corpus"
_STUB_EFFECT = "standard"
_STUB_THREAT_TYPE = "harm"
_STUB_BASE_MAGNITUDE = Magnitude.STANDARD  # 2


class ResolutionNode:
    """Deterministic resolution (decisions #7, #15-17): pick the attribute (stub),
    roll its pool, and scale the pre-set threat by the result. No LLM — the dice
    and scaling come straight from the Phase-0 mechanics core.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng

    async def __call__(self, state: GraphState) -> dict:
        attribute = _STUB_ATTRIBUTE
        rating = int(getattr(state, attribute, 0))
        result = roll_pool(rating, rng=self._rng)
        outcome = scale_threat(int(_STUB_BASE_MAGNITUDE), result.tier, Position.RISKY)

        return {
            "attribute": attribute,
            "effect": _STUB_EFFECT,
            "threat_type": _STUB_THREAT_TYPE,
            "threat_channel": attribute,
            "base_magnitude": int(_STUB_BASE_MAGNITUDE),
            "roll_dice": list(result.dice),
            "roll_tier": result.tier.value,
            "landed_magnitude": outcome.landed_magnitude,
            "outcome_avoided": outcome.avoided,
            "outcome_crit": outcome.crit,
        }
