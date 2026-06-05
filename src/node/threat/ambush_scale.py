from dataclasses import replace

from src.core.mechanic.magnitude import clamp_magnitude
from src.core.mechanic.scaling import Outcome
from src.state import GraphState


class AmbushScaleNode:
    """The world-acts mirror of dice_scale. There is no player action roll to
    scale against — an ambush from a hostile creature simply lands at its full
    (already danger-capped) magnitude, and the player mitigates via the resist
    cycle. No apply_effect (the player attacked nothing)."""

    async def __call__(self, state: GraphState) -> dict:
        landed = [
            replace(
                t,
                outcome=Outcome(
                    landed_magnitude=clamp_magnitude(magnitude=int(t.magnitude)),
                    avoided=False,
                    crit=False,
                ),
            )
            for t in state.get("threats", [])
        ]
        return {"threats": landed}
