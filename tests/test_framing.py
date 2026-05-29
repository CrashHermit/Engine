import asyncio
import random

from src.core.model.message import Message
from src.graph.main_graph import MainGraphBuilder, _FRAMING_NODES
from src.nodes.framing import (
    AttributeSelectorNode,
    EffectClassifierNode,
    ThreatChannelClassifierNode,
    ThreatMagnitudeClassifierNode,
    ThreatTypeClassifierNode,
)
from src.nodes.resolution import ResolutionNode
from src.state import GraphState


def _run(coro):
    return asyncio.run(coro)


def _state(**kwargs) -> GraphState:
    base = {"human_message": Message(role="human", content="strike the guard")}
    base.update(kwargs)
    return GraphState(**base)


class _FakeProgram:
    """Stand-in for a DSPy Predict program — returns fixed prediction fields."""

    def __init__(self, **fields):
        self._fields = fields

    async def aforward(self, **_kwargs):
        return type("Prediction", (), self._fields)()


def _with_program(node, **fields):
    node._program = _FakeProgram(**fields)
    return node


# --- the graph wires the full fan-out -------------------------------------

def test_main_graph_compiles_with_fan_out():
    graph = MainGraphBuilder().build()
    nodes = set(graph.get_graph().nodes.keys())
    for name in _FRAMING_NODES:
        assert name in nodes
    assert {"roll_gate", "segmenter", "resolution", "narrator"} <= nodes


# --- each classifier normalises its output to the shared vocabulary -------

def test_attribute_selector_normalises():
    node = _with_program(AttributeSelectorNode(), attribute="mens")
    assert _run(node(_state()))["attribute"] == "mens"


def test_effect_classifier_normalises():
    node = _with_program(EffectClassifierNode(), effect="great")
    assert _run(node(_state()))["effect"] == "great"


def test_threat_type_classifier_normalises():
    node = _with_program(ThreatTypeClassifierNode(), threat_type="failure_of_goal")
    assert _run(node(_state()))["threat_type"] == "failure_of_goal"


def test_threat_channel_classifier_normalises():
    node = _with_program(ThreatChannelClassifierNode(), channel="anima")
    assert _run(node(_state()))["threat_channel"] == "anima"


def test_threat_magnitude_clamps_into_1_to_4():
    node = _with_program(ThreatMagnitudeClassifierNode(), magnitude=9)
    assert _run(node(_state()))["base_magnitude"] == 4

    node = _with_program(ThreatMagnitudeClassifierNode(), magnitude=0)
    assert _run(node(_state()))["base_magnitude"] == 1  # never a 0 "threat"


# --- the five classifiers write disjoint keys (safe parallel fan-out) -----

def test_framing_nodes_write_disjoint_keys():
    nodes = [
        _with_program(AttributeSelectorNode(), attribute="corpus"),
        _with_program(EffectClassifierNode(), effect="standard"),
        _with_program(ThreatTypeClassifierNode(), threat_type="harm"),
        _with_program(ThreatMagnitudeClassifierNode(), magnitude=2),
        _with_program(ThreatChannelClassifierNode(), channel="corpus"),
    ]
    seen: set[str] = set()
    for node in nodes:
        keys = set(_run(node(_state())).keys())
        assert seen.isdisjoint(keys), f"key collision in fan-out: {seen & keys}"
        seen |= keys
    assert seen == {"attribute", "effect", "threat_type", "base_magnitude", "threat_channel"}


# --- resolution joins the fan-out by reading framing from state -----------

def test_resolution_reads_attribute_and_magnitude_from_state():
    node = ResolutionNode(rng=random.Random(0))
    state = _state(attribute="anima", anima=2, base_magnitude=4)
    out = _run(node(state))
    assert len(out["roll_dice"]) == 2  # anima rating 2 -> 2 dice
    assert 0 <= out["landed_magnitude"] <= 4


def test_resolution_falls_back_when_framing_missing():
    node = ResolutionNode(rng=random.Random(0))
    out = _run(node(_state(corpus=1)))  # no attribute/base_magnitude in state
    assert out["roll_tier"] is not None
    assert len(out["roll_dice"]) == 1  # default attribute corpus, rating 1
