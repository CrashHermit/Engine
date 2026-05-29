import asyncio
import random

from src.core.mechanics.dice import RollTier
from src.core.model.message import Message
from src.graph.main_graph import MainGraphBuilder
from src.nodes.narrator import format_outcome
from src.nodes.resolution import ResolutionNode
from src.state import GraphState


def _run(coro):
    return asyncio.run(coro)


def _state(**kwargs) -> GraphState:
    base = {"human_message": Message(role="human", content="act")}
    base.update(kwargs)
    return GraphState(**base)


def test_main_graph_compiles():
    # Catches wiring errors in the rewired topology (conditional edges, node names).
    graph = MainGraphBuilder().build()
    assert graph is not None


def test_resolution_node_invariants():
    node = ResolutionNode(rng=random.Random(0))
    # Framing comes from state now (set by the fan-out classifiers upstream).
    state = _state(attribute="corpus", corpus=3, base_magnitude=2)
    for _ in range(50):
        out = _run(node(state))
        assert out["roll_tier"] in {t.value for t in RollTier}
        assert len(out["roll_dice"]) == 3  # rating 3 -> 3 dice
        assert 0 <= out["landed_magnitude"] <= 2  # cannot exceed the base magnitude
        assert isinstance(out["outcome_avoided"], bool)


def test_resolution_zero_rating_uses_two_dice():
    node = ResolutionNode(rng=random.Random(1))
    out = _run(node(_state(attribute="corpus", corpus=0)))
    assert len(out["roll_dice"]) == 2  # 0-rating -> roll 2d6, take worst


def test_format_outcome_empty_without_roll():
    assert format_outcome(_state(needs_roll=False)) == ""
    assert format_outcome(_state(needs_roll=None)) == ""


def test_format_outcome_avoided_and_crit():
    crit = format_outcome(_state(needs_roll=True, outcome_avoided=True, outcome_crit=True))
    assert "advantage" in crit
    clean = format_outcome(_state(needs_roll=True, outcome_avoided=True, outcome_crit=False))
    assert "avoided" in clean


def test_format_outcome_landed_harm():
    text = format_outcome(
        _state(
            needs_roll=True,
            outcome_avoided=False,
            landed_magnitude=2,
            threat_type="harm",
            threat_channel="corpus",
        )
    )
    assert "standard" in text and "harm" in text


def test_format_outcome_reduced_to_nothing():
    text = format_outcome(_state(needs_roll=True, outcome_avoided=False, landed_magnitude=0))
    assert "nothing" in text
