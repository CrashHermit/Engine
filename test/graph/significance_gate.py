from __future__ import annotations

import pytest

from src.core.mechanic.scaling import Outcome, Position
from src.core.model.threat import Channel, Threat, ThreatType
from src.graph.routers import route_by_significance
from src.state import GraphState


def _state_with(landed: int, *, avoided: bool = False) -> GraphState:
    # The gate now reads per-threat outcomes via state.landed_threats, so build
    # a single scaled threat carrying the outcome under test.
    threat = Threat(
        source="warden",
        type=ThreatType.HARM,
        channel=Channel.CORPUS,
        magnitude=landed or 1,
        position=Position.RISKY,
        outcome=Outcome(landed_magnitude=landed, avoided=avoided, crit=False),
    )
    return GraphState(threats=[threat])


@pytest.mark.parametrize(
    "landed, avoided, expected",
    [
        (0, True, "final_planner"),  # clean/crit avoid → no resist offer
        (1, False, "held_planner"),  # Minor still lands → resist offer
        (2, False, "held_planner"),  # Standard
        (4, False, "held_planner"),  # Fatal
    ],
)
def test_route_by_significance(landed: int, avoided: bool, expected: str):
    assert route_by_significance(_state_with(landed, avoided=avoided)) == expected


def test_route_by_significance_handles_no_threats():
    assert route_by_significance(GraphState()) == "final_planner"
