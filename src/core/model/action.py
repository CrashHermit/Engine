from dataclasses import dataclass

from src.core.model.entity import ThreatPillar
from src.core.model.threat import Channel


@dataclass(frozen=True)
class ActionIntent:
    """The player's single action, read as one cohesive value: which attribute
    it rolls, what it targets, which pillar it attacks, and whether it's pushed.

    A *view* over GraphState's flat framing fields (each written by its own
    classifier), built on demand via GraphState.action_intent — consumers read
    the bundle instead of reaching into four separate fields. `pillar` is always
    a concrete pillar (defaults to EXISTS), so callers need not re-resolve it.
    """

    attribute: Channel | None
    target: str
    pillar: ThreatPillar
    push: bool
