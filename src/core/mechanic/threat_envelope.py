from src.core.mechanic.magnitude import Magnitude
from src.core.mechanic.scaling import Position
from src.core.model.entity import Danger
from src.core.model.threat import Channel, Threat

# Per-source ceiling (decision: ceiling is per-source, never a scene max).
DANGER_MAGNITUDE_CAP: dict[Danger, Magnitude] = {
    Danger.LOW: Magnitude.STANDARD,
    Danger.STANDARD: Magnitude.SEVERE,
    Danger.ELITE: Magnitude.FATAL,
    Danger.DEADLY: Magnitude.FATAL,
}
ENVIRONMENT_CAP: Magnitude = Magnitude.FATAL  # no-entity threats are uncapped

DANGER_POSITION: dict[Danger, Position] = {
    Danger.LOW: Position.CONTROLLED,
    Danger.STANDARD: Position.RISKY,
    Danger.ELITE: Position.DESPERATE,
    Danger.DEADLY: Position.DESPERATE,
}


def magnitude_cap_for(danger: Danger | None) -> Magnitude:
    return ENVIRONMENT_CAP if danger is None else DANGER_MAGNITUDE_CAP[danger]


def position_for(danger: Danger | None) -> Position:
    return Position.RISKY if danger is None else DANGER_POSITION[danger]


def snap_channel(predicted: Channel, affinity: frozenset[Channel]) -> Channel:
    """Anchor the classifier's channel into the source's affinity (belt-and-suspenders).

    Empty affinity (environment) leaves the prediction untouched.
    """
    if not affinity or predicted in affinity:
        return predicted
    return sorted(affinity)[0]


def describe_threat(threat: Threat | None) -> str:
    """Return a consequence label for offers, parser context, and resolution."""
    if threat is None:
        return ""
    mag = threat.outcome.landed_magnitude if threat.outcome else int(threat.magnitude)
    mag_label = Magnitude(mag).name.lower() if mag > 0 else "minor"
    return (
        f"{mag_label} {threat.type.value} ({threat.channel.value}) "
        f"from the {threat.source}"
    )
