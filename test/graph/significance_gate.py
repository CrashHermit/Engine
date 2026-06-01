import pytest

from src.core.mechanic.scaling import Outcome
from src.graph.resolution_graph import _route_by_significance
from src.state import GraphState


def _state_with(landed: int, *, avoided: bool = False) -> GraphState:
    return GraphState(outcome=Outcome(landed_magnitude=landed, avoided=avoided, crit=False))


@pytest.mark.parametrize(
    "landed, avoided, expected",
    [
        (0, True, "final_planner"),   # clean/crit avoid → no resist offer
        (1, False, "held_planner"),   # Minor still lands → resist offer
        (2, False, "held_planner"),   # Standard
        (4, False, "held_planner"),   # Fatal
    ],
)
def test_route_by_significance(landed: int, avoided: bool, expected: str):
    assert _route_by_significance(_state_with(landed, avoided=avoided)) == expected


def test_route_by_significance_handles_missing_outcome():
    assert _route_by_significance(GraphState()) == "final_planner"
