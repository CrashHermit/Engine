"""Pure, deterministic resolution mechanics (no LLM, no graph, no DB).

The balance-critical core of the Blades-in-the-Dark cherry-pick: dice, outcome
scaling, push/resist cost, persistent harm, and the stress economy. Every tunable
number is a default parameter, so "deferred to playtest" never blocks building.
See `docs/bitd-integration-design.md` for the decisions these implement.
"""

from src.core.mechanics.dice import (
    ATTRIBUTE_CAP,
    RollResult,
    RollTier,
    classify,
    result_from_dice,
    roll_pool,
)
from src.core.mechanics.economy import (
    DEFAULT_STRESS_MAX,
    DEFAULT_TRAUMA_MAX,
    EconomyConfig,
    StressResult,
    ViceResult,
    add_stress,
    vice_clear,
)
from src.core.mechanics.harm import (
    DEFAULT_CAPACITY,
    WoundPool,
    WoundThresholds,
    distal_parts,
)
from src.core.mechanics.magnitude import (
    MAX_MAGNITUDE,
    MIN_MAGNITUDE,
    Magnitude,
    clamp_magnitude,
)
from src.core.mechanics.push import improve_magnitude, push_cost
from src.core.mechanics.scaling import Outcome, Position, scale_threat

__all__ = [
    "ATTRIBUTE_CAP",
    "RollResult",
    "RollTier",
    "classify",
    "result_from_dice",
    "roll_pool",
    "Magnitude",
    "MIN_MAGNITUDE",
    "MAX_MAGNITUDE",
    "clamp_magnitude",
    "Outcome",
    "Position",
    "scale_threat",
    "push_cost",
    "improve_magnitude",
    "WoundPool",
    "WoundThresholds",
    "DEFAULT_CAPACITY",
    "distal_parts",
    "EconomyConfig",
    "StressResult",
    "ViceResult",
    "add_stress",
    "vice_clear",
    "DEFAULT_STRESS_MAX",
    "DEFAULT_TRAUMA_MAX",
]
