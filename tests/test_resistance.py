import asyncio
import random

from src.core.model.message import Message
from src.nodes.resistance import ResistParserNode, ResistResolutionNode
from src.state import GraphState


def _run(coro):
    return asyncio.run(coro)


def _state(**kwargs) -> GraphState:
    base = {"human_message": Message(role="human", content="I brace against it")}
    base.update(kwargs)
    return GraphState(**base)


class _FakeProgram:
    def __init__(self, **fields):
        self._fields = fields

    async def aforward(self, **_kwargs):
        return type("Prediction", (), self._fields)()


def test_resist_parser_reads_decision():
    node = ResistParserNode()
    node._program = _FakeProgram(is_resisting=True)
    out = _run(node(_state(resistance_history=[Message(role="ai", content="a blade bites your arm")])))
    assert out["resist_decision"] is True


def test_resist_resolution_declined_costs_nothing():
    node = ResistResolutionNode(rng=random.Random(0))
    out = _run(node(_state(resist_decision=False, landed_magnitude=3)))
    assert out["stress_delta"] == 0
    assert "landed_magnitude" not in out  # consequence stands unchanged


def test_resist_resolution_reduces_magnitude_and_sets_cost():
    node = ResistResolutionNode(rng=random.Random(0))
    state = _state(
        resist_decision=True,
        threat_channel="corpus",
        corpus=2,
        landed_magnitude=3,
    )
    out = _run(node(state))
    assert out["landed_magnitude"] == 2  # always reduced one step
    assert out["stress_delta"] in (0, 1, 2, 3)  # flat cost by push tier
    assert len(out["roll_dice"]) == 2  # corpus rating 2


def test_resist_resolution_clamps_at_zero():
    node = ResistResolutionNode(rng=random.Random(1))
    out = _run(node(_state(resist_decision=True, threat_channel="anima", anima=1, landed_magnitude=0)))
    assert out["landed_magnitude"] == 0
